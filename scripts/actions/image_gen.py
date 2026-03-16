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
import requests
from datetime import datetime, timezone


GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_IMAGE_MODEL = "gemini-2.0-flash-exp"

# DALL-E is BANNED — removed 2026-03-16. Gemini only.


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

def generate_image(prompt: str, aspect_ratio: str = "16:9") -> dict:
    """Generate an image using Gemini ONLY. No fallback. No DALL-E.

    If Gemini fails, generation fails. This is intentional — DALL-E produces
    cartoonish output that damages brand credibility. Better to skip an image
    than post garbage.

    Args:
        prompt:       Text description of the image to generate.
        aspect_ratio: "1:1", "16:9", "9:16", "4:5", "4:3", or "3:4".

    Returns:
        {"image_bytes": bytes, "mime_type": str, "provider": str}
    """
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY not set. DALL-E is BANNED — Gemini is the only image provider.")

    result = _generate_gemini(prompt, aspect_ratio)
    print(f"    [Gemini] Success")
    return result


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
    # IMPORTANT: DALL-E ignores negative prompts ("NO phones").
    # Describe ONLY what to show. Never mention phones/devices even as negatives.
    prompt = (
        f"Photorealistic editorial photograph of a clean minimalist workspace. "
        f"A wooden desk surface with a ceramic coffee mug, a succulent plant in a "
        f"terracotta pot, and soft morning sunlight streaming through linen curtains. "
        f"Warm amber tones, shallow depth of field with creamy bokeh background. "
        f"Shot on Canon EOS R5 with 35mm f/1.4 lens. Kodak Portra 400 film emulation. "
        f"Fine organic grain, natural color, editorial magazine quality. "
        f"The scene evokes trust, care, and attention to detail. "
        f"Wide 16:9 composition. IMG_7291.CR3 unedited RAW photograph."
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
