"""
Image generation wrapper for GadgetGeeks Marketing Organization.

Primary: Google Gemini API for image generation.
Fallback: NONE — DALL-E is BANNED. If Gemini fails, generation fails. No silent fallback.
Hosting: Shopify staged uploads for CDN hosting.

RULE: OpenAI DALL-E produces cartoonish/stylized images that damage brand credibility.
DALL-E fallback was removed 2026-03-16. Gemini-only. No exceptions.
"""

import base64
import json
import os
import time
import requests
from datetime import datetime, timezone
from pathlib import Path


GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_IMAGE_MODEL = "gemini-2.0-flash-exp"

# DALL-E is BANNED — removed 2026-03-16. Gemini only.

# Max retries before falling back to pre-uploaded fallback images
GEMINI_MAX_RETRIES = 2
GEMINI_RETRY_DELAY_SECONDS = 3

# Fallback images config path
FALLBACK_IMAGES_PATH = Path(__file__).parent.parent.parent / "config" / "fallback-images.json"


# ---------------------------------------------------------------------------
# Fallback image loader
# ---------------------------------------------------------------------------

def _load_fallback_images() -> dict:
    """Load fallback images config from config/fallback-images.json."""
    if not FALLBACK_IMAGES_PATH.exists():
        return {}
    try:
        data = json.loads(FALLBACK_IMAGES_PATH.read_text(encoding="utf-8"))
        return data.get("categories", {})
    except Exception as e:
        print(f"    [Fallback] WARNING: Could not load fallback images config: {e}")
        return {}


def get_fallback_image(category: str) -> dict | None:
    """Get a fallback image for the given blog category.

    Downloads the pre-uploaded Shopify CDN image and returns it in the
    same format as generate_image().

    Returns None if no fallback is available or download fails.
    """
    categories = _load_fallback_images()
    if not categories:
        print("    [Fallback] No fallback images config found")
        return None

    # Normalize category to match config keys
    cat_key = category.lower().replace(" ", "-").strip()
    fallback = categories.get(cat_key) or categories.get("default")
    if not fallback:
        print(f"    [Fallback] No fallback image for category '{category}'")
        return None

    url = fallback.get("url", "")
    if not url:
        print(f"    [Fallback] Fallback entry for '{cat_key}' has no URL")
        return None

    try:
        resp = requests.get(url, timeout=30)
        if resp.ok:
            print(f"    [Fallback] Using fallback image for category '{cat_key}': {url}")
            return {
                "image_bytes": resp.content,
                "mime_type": resp.headers.get("Content-Type", "image/png"),
                "provider": "fallback_cdn",
                "fallback_url": url,
            }
        else:
            print(f"    [Fallback] CDN download failed ({resp.status_code}) for: {url}")
            return None
    except Exception as e:
        print(f"    [Fallback] CDN download error: {e}")
        return None


# ---------------------------------------------------------------------------
# Gemini image generation
# ---------------------------------------------------------------------------

def _generate_gemini(prompt: str, aspect_ratio: str = "16:9") -> dict:
    """Generate an image using Gemini. Raises on failure."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")

    url = f"{GEMINI_API_BASE}/models/{GEMINI_IMAGE_MODEL}:generateContent"

    generation_prompt = (
        f"{prompt}\n\n"
        f"Generate this as a {aspect_ratio} aspect ratio image. "
        f"Photorealistic, high quality, no text overlays, no watermarks."
    )

    resp = requests.post(
        url,
        params={"key": api_key},
        headers={"Content-Type": "application/json"},
        json={
            "contents": [
                {
                    "parts": [{"text": generation_prompt}]
                }
            ],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
            },
        },
        timeout=120,
    )
    if not resp.ok:
        err_body = resp.text[:500]
        raise RuntimeError(f"{resp.status_code} {resp.reason}: {err_body}")
    data = resp.json()

    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {data}")

    parts = candidates[0].get("content", {}).get("parts", [])

    for part in parts:
        inline_data = part.get("inlineData")
        if inline_data and inline_data.get("data"):
            mime_type = inline_data.get("mimeType", "image/png")
            image_b64 = inline_data["data"]
            return {
                "image_bytes": base64.b64decode(image_b64),
                "mime_type": mime_type,
                "provider": "gemini",
            }

    raise RuntimeError(f"Gemini returned no image data. Parts: {[list(p.keys()) for p in parts]}")


# ---------------------------------------------------------------------------
# OpenAI DALL-E — PERMANENTLY REMOVED (2026-03-16)
# Reason: Produces cartoonish/stylized images. Cost money and reputation.
# DALL-E is BANNED from this organization. Gemini only.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Main generate function — tries Gemini, falls back to DALL-E
# ---------------------------------------------------------------------------

def generate_image(prompt: str, aspect_ratio: str = "16:9",
                    category: str = "default") -> dict:
    """Generate an image using Gemini with retries. Falls back to pre-uploaded
    CDN images if Gemini fails after GEMINI_MAX_RETRIES attempts.

    DALL-E is BANNED. The only fallback is pre-uploaded Shopify CDN images
    from config/fallback-images.json — real product photos, not AI slop.

    Args:
        prompt:       Text description of the image to generate.
        aspect_ratio: "1:1", "16:9", "9:16", "4:5", "4:3", or "3:4".
        category:     Blog category for fallback image selection.

    Returns:
        {"image_bytes": bytes, "mime_type": str, "provider": str}
    """
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        print("    [Gemini] GEMINI_API_KEY not set — trying fallback images")
        fallback = get_fallback_image(category)
        if fallback:
            return fallback
        raise ValueError("GEMINI_API_KEY not set and no fallback image available.")

    last_error = None
    for attempt in range(1, GEMINI_MAX_RETRIES + 1):
        try:
            result = _generate_gemini(prompt, aspect_ratio)
            print(f"    [Gemini] Success on attempt {attempt}")
            return result
        except Exception as e:
            last_error = e
            print(f"    [Gemini] Attempt {attempt}/{GEMINI_MAX_RETRIES} failed: {e}")
            if attempt < GEMINI_MAX_RETRIES:
                print(f"    [Gemini] Retrying in {GEMINI_RETRY_DELAY_SECONDS}s...")
                time.sleep(GEMINI_RETRY_DELAY_SECONDS)

    # All retries exhausted — try fallback CDN image
    print(f"    [Gemini] All {GEMINI_MAX_RETRIES} attempts failed. Trying fallback image for category '{category}'...")
    fallback = get_fallback_image(category)
    if fallback:
        print(f"    [Fallback] Using pre-uploaded CDN image instead of AI generation")
        return fallback

    # No fallback available — raise the last error
    raise RuntimeError(
        f"Gemini failed after {GEMINI_MAX_RETRIES} retries and no fallback image available. "
        f"Last error: {last_error}"
    )


# ---------------------------------------------------------------------------
# Blog header helper
# ---------------------------------------------------------------------------

def generate_blog_header(blog_title: str, blog_topic: str) -> dict:
    """Get a blog header image that MATCHES the blog topic.

    RULES:
    1. If the blog is about a specific product (iPhone, Samsung, etc.),
       use the REAL product photo from assets/product-photos/.
       NEVER generate phones/devices with AI.
    2. Only use AI-generated scenes for non-product blogs (buying guides,
       general tips, industry news) where no specific device is featured.
    3. The image MUST relate to the blog content. No generic desk scenes
       for product-specific blogs.

    Returns:
        {"image_bytes": bytes, "mime_type": str, "provider": str}
    """
    title_lower = blog_title.lower()
    topic_lower = blog_topic.lower()
    combined = f"{title_lower} {topic_lower}"

    # --- Check for product-specific blogs: use REAL product photos from Shopify CDN ---
    product_photo_cdn = {
        "iphone 14": "https://cdn.shopify.com/s/files/1/0664/1664/0251/files/apple-iphone-14-desktop.png",
        "iphone 13": "https://cdn.shopify.com/s/files/1/0664/1664/0251/files/apple-iphone-13-pos1-floating_074be56b-89cc-46d2-a70a-69f2e1e25b7c.png?v=1773615063",
        "iphone 12": "https://cdn.shopify.com/s/files/1/0664/1664/0251/files/apple-iphone-12-pos1-floating_583ba2cf-31e5-4a1e-abc0-b203bcb0b4f8.png?v=1773615636",
    }

    for keyword, cdn_url in product_photo_cdn.items():
        if keyword in combined:
            print(f"    [Blog Header] Using REAL product photo from Shopify CDN: {keyword}")
            resp = requests.get(cdn_url, timeout=30)
            if resp.ok:
                return {
                    "image_bytes": resp.content,
                    "mime_type": "image/png",
                    "provider": "real_product_photo",
                }
            print(f"    [Blog Header] WARNING: CDN fetch failed ({resp.status_code}), falling back to AI scene")
            break

    # --- Non-product blog: generate a relevant AI scene (NO devices) ---
    # Build a prompt that relates to the actual blog topic
    prompt = (
        f"Photorealistic editorial photograph that evokes the theme: {blog_title}. "
        f"Clean composition, no phones, no devices, no screens, no text, no logos. "
        f"Scene and mood only — environment, lighting, atmosphere that matches the topic. "
        f"Shot on Canon EOS R5 with 35mm f/1.4 lens. Kodak Portra 400 film emulation. "
        f"Fine organic grain, natural color, editorial magazine quality. "
        f"Wide 16:9 composition. IMG_7291.CR3 unedited RAW photograph."
    )
    # Map blog_topic to a fallback category for the CDN fallback system
    category = "default"
    if any(kw in topic_lower for kw in ("guide", "buying", "best", "top", "comparison")):
        category = "buying-guide"
    elif any(kw in topic_lower for kw in ("how", "setup", "tip", "fix", "troubleshoot")):
        category = "how-to"
    elif any(kw in topic_lower for kw in ("review", "spotlight", "product")):
        category = "product"
    elif any(kw in topic_lower for kw in ("lifestyle", "daily", "student", "work")):
        category = "lifestyle"
    elif any(kw in topic_lower for kw in ("news", "trend", "update", "announce")):
        category = "news"
    return generate_image(prompt, aspect_ratio="16:9", category=category)


# ---------------------------------------------------------------------------
# Shopify upload (stagedUploadsCreate -> fileCreate)
# ---------------------------------------------------------------------------

def _get_shopify_token() -> str:
    """Get a valid Shopify access token via client credentials."""
    static = os.environ.get("SHOPIFY_ACCESS_TOKEN", "")
    if static:
        return static

    store = os.environ.get("SHOPIFY_STORE", "gadgetgeekspro.myshopify.com")
    client_id = os.environ.get("SHOPIFY_CLIENT_ID", "")
    client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET", "")

    resp = requests.post(
        f"https://{store}/admin/oauth/access_token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=15,
    )
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise RuntimeError("No access_token in Shopify token response")
    return token


def _shopify_graphql(query: str, variables: dict = None, token: str = None) -> dict:
    """Execute a Shopify Admin GraphQL request."""
    store = os.environ.get("SHOPIFY_STORE", "gadgetgeekspro.myshopify.com")
    token = token or _get_shopify_token()
    url = f"https://{store}/admin/api/2026-01/graphql.json"

    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    resp = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": token,
        },
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return data.get("data", data)


def upload_to_shopify(image_bytes: bytes, filename: str,
                      content_type: str = "image/png") -> str:
    """Upload raw image bytes to Shopify Files via staged uploads.

    Args:
        image_bytes:  Raw image bytes.
        filename:     Desired filename (e.g. "blog-header-activation-lock.png").
        content_type: MIME type of the image.

    Returns:
        The Shopify CDN URL of the uploaded file.
    """
    token = _get_shopify_token()

    # --- Step 1: Create a staged upload target ---
    staged_mutation = """
mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
  stagedUploadsCreate(input: $input) {
    stagedTargets {
      url
      resourceUrl
      parameters {
        name
        value
      }
    }
    userErrors { field message }
  }
}
"""
    staged_vars = {
        "input": [
            {
                "resource": "FILE",
                "filename": filename,
                "mimeType": content_type,
                "httpMethod": "POST",
            }
        ]
    }

    staged_data = _shopify_graphql(staged_mutation, staged_vars, token=token)
    targets = staged_data.get("stagedUploadsCreate", {}).get("stagedTargets", [])
    user_errors = staged_data.get("stagedUploadsCreate", {}).get("userErrors", [])

    if user_errors:
        msgs = "; ".join(f"{e['field']}: {e['message']}" for e in user_errors)
        raise RuntimeError(f"stagedUploadsCreate failed: {msgs}")

    if not targets:
        raise RuntimeError("No staged upload targets returned")

    target = targets[0]
    upload_url = target["url"]
    resource_url = target["resourceUrl"]
    params = {p["name"]: p["value"] for p in target.get("parameters", [])}

    # --- Step 2: Upload to the staged target ---
    files = {"file": (filename, image_bytes, content_type)}
    upload_resp = requests.post(
        upload_url,
        data=params,
        files=files,
        timeout=120,
    )
    upload_resp.raise_for_status()

    # --- Step 3: Create the file in Shopify ---
    file_create_mutation = """
mutation fileCreate($files: [FileCreateInput!]!) {
  fileCreate(files: $files) {
    files {
      id
      alt
      createdAt
      ... on MediaImage {
        image { url }
      }
    }
    userErrors { field message }
  }
}
"""
    file_vars = {
        "files": [
            {
                "alt": filename.replace("-", " ").replace("_", " ").rsplit(".", 1)[0],
                "contentType": "IMAGE",
                "originalSource": resource_url,
            }
        ]
    }

    file_data = _shopify_graphql(file_create_mutation, file_vars, token=token)
    file_errors = file_data.get("fileCreate", {}).get("userErrors", [])
    if file_errors:
        msgs = "; ".join(f"{e['field']}: {e['message']}" for e in file_errors)
        raise RuntimeError(f"fileCreate failed: {msgs}")

    created_files = file_data.get("fileCreate", {}).get("files", [])
    if not created_files:
        raise RuntimeError("No files returned from fileCreate")

    cdn_url = ""
    f = created_files[0]
    if "image" in f and f["image"]:
        cdn_url = f["image"].get("url", "")

    # If image URL isn't available yet (processing), fall back to resource URL
    if not cdn_url:
        cdn_url = resource_url

    return cdn_url
