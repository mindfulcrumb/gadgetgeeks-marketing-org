"""
Image generation wrapper for GadgetGeeks Marketing Organization.

Primary: Google Gemini API for image generation.
Fallback: OpenAI DALL-E 3 when Gemini quota is exhausted (429).
Hosting: Shopify staged uploads for CDN hosting.
"""

import base64
import json
import os
import requests
from datetime import datetime, timezone


GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_IMAGE_MODEL = "gemini-2.0-flash-exp"

# Aspect ratio to DALL-E 3 size mapping
DALLE_SIZE_MAP = {
    "1:1": "1024x1024",
    "16:9": "1792x1024",
    "9:16": "1024x1792",
    "4:5": "1024x1024",   # DALL-E doesn't support 4:5, use square
    "4:3": "1792x1024",   # closest wide format
    "3:4": "1024x1792",   # closest tall format
}


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
# OpenAI DALL-E 3 fallback
# ---------------------------------------------------------------------------

def _generate_openai(prompt: str, aspect_ratio: str = "16:9") -> dict:
    """Generate an image using OpenAI DALL-E 3. Raises on failure."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set — cannot use DALL-E fallback")

    size = DALLE_SIZE_MAP.get(aspect_ratio, "1024x1024")

    # Trim prompt for DALL-E (4000 char limit) and add quality instructions
    dalle_prompt = prompt[:3500] + (
        "\n\nPhotorealistic photograph. High quality. "
        "No text overlays, no watermarks, no logos."
    )

    resp = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "dall-e-3",
            "prompt": dalle_prompt,
            "n": 1,
            "size": size,
            "quality": "hd",
            "response_format": "b64_json",
        },
        timeout=120,
    )
    if not resp.ok:
        err_body = resp.text[:500]
        raise RuntimeError(f"DALL-E {resp.status_code}: {err_body}")

    data = resp.json()
    images = data.get("data", [])
    if not images or "b64_json" not in images[0]:
        raise RuntimeError(f"DALL-E returned no image data: {data}")

    return {
        "image_bytes": base64.b64decode(images[0]["b64_json"]),
        "mime_type": "image/png",
        "provider": "openai_dalle3",
    }


# ---------------------------------------------------------------------------
# Main generate function — tries Gemini, falls back to DALL-E
# ---------------------------------------------------------------------------

def generate_image(prompt: str, aspect_ratio: str = "16:9") -> dict:
    """Generate an image. Tries Gemini first, falls back to OpenAI DALL-E 3.

    Args:
        prompt:       Text description of the image to generate.
        aspect_ratio: "1:1", "16:9", "9:16", "4:5", "4:3", or "3:4".

    Returns:
        {"image_bytes": bytes, "mime_type": str, "provider": str}
    """
    # Try Gemini first
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if gemini_key:
        try:
            result = _generate_gemini(prompt, aspect_ratio)
            print(f"    [Gemini] Success")
            return result
        except (RuntimeError, Exception) as e:
            print(f"    [Gemini] Failed: {str(e)[:200]} — trying DALL-E fallback...")

    # Fallback to OpenAI DALL-E 3
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        try:
            result = _generate_openai(prompt, aspect_ratio)
            print(f"    [DALL-E 3] Success")
            return result
        except Exception as e:
            raise RuntimeError(f"Both Gemini and DALL-E failed. DALL-E error: {e}")

    # Neither key available
    if not gemini_key and not openai_key:
        raise ValueError("No image generation API key set (GEMINI_API_KEY or OPENAI_API_KEY)")

    # Only Gemini was available and it failed
    raise RuntimeError("Gemini quota exceeded and OPENAI_API_KEY not configured as fallback")


# ---------------------------------------------------------------------------
# Blog header helper
# ---------------------------------------------------------------------------

def generate_blog_header(blog_title: str, blog_topic: str) -> dict:
    """Generate a photorealistic blog header image.

    RULES — NEVER VIOLATE:
    - NO phones, NO devices, NO screens in the image
    - NO text, NO documents, NO readable writing, NO UI elements
    - NO logos, NO watermarks, NO brand names
    - Scene ONLY: environment, lighting, mood, atmosphere
    - The image should FEEL like the topic without literally showing products

    Returns:
        {"image_bytes": bytes, "mime_type": str}
    """
    prompt = (
        f"Photorealistic editorial photograph that evokes the mood of: {blog_topic}. "
        f"Clean, modern environment shot. NO phones, NO devices, NO screens, NO text, "
        f"NO documents, NO readable writing, NO packaging with labels, NO UI elements. "
        f"Show ONLY: a clean workspace, natural materials, ambient environment, or abstract "
        f"textures that suggest the topic through mood and atmosphere. "
        f"Shallow depth of field, shot on Canon EOS R5 with 35mm f/1.4 lens. "
        f"Soft natural window light, muted color palette with teal-and-amber grade. "
        f"Kodak Portra 400 film emulation, fine organic grain. "
        f"No text, no watermarks, no logos, no phones, no screens. "
        f"Wide 16:9 editorial blog header. IMG_7291.CR3 unedited RAW."
    )
    return generate_image(prompt, aspect_ratio="16:9")


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
