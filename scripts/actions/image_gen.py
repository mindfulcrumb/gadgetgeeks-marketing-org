"""
Image generation wrapper for GadgetGeeks Marketing Organization.

Uses OpenAI DALL-E 3 for generation and Shopify's staged uploads for hosting.
"""

import json
import os
import requests
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# DALL-E 3 generation
# ---------------------------------------------------------------------------

def generate_image(
    prompt: str,
    size: str = "1792x1024",
    quality: str = "hd",
) -> dict:
    """Generate an image using OpenAI DALL-E 3.

    Args:
        prompt:  Text description of the image to generate.
        size:    Image dimensions — "1024x1024", "1792x1024", or "1024x1792".
        quality: "standard" or "hd".

    Returns:
        {"url": "<temporary_url>", "revised_prompt": "<model_revised_prompt>"}
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    resp = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "dall-e-3",
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": 1,
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    image_data = data["data"][0]
    return {
        "url": image_data["url"],
        "revised_prompt": image_data.get("revised_prompt", prompt),
    }


# ---------------------------------------------------------------------------
# Blog header helper
# ---------------------------------------------------------------------------

def generate_blog_header(blog_title: str, blog_topic: str) -> dict:
    """Generate a photorealistic blog header image for a given blog post.

    Args:
        blog_title: The title of the blog post.
        blog_topic: A short description of the blog's topic/category.

    Returns:
        {"url": "<temporary_url>", "revised_prompt": "<model_revised_prompt>"}
    """
    prompt = (
        f"Photorealistic editorial photograph for a tech blog article titled "
        f'"{blog_title}". '
        f"Topic: {blog_topic}. "
        f"Clean, modern composition with soft natural lighting. "
        f"Shallow depth of field, shot on Sony A7IV with 35mm f/1.4 lens. "
        f"Muted color palette with a slight teal-and-amber grade. "
        f"No text, no watermarks, no logos. "
        f"Suitable as a wide 16:9 blog header image."
    )
    return generate_image(prompt, size="1792x1024", quality="hd")


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


def upload_to_shopify(image_url: str, filename: str) -> str:
    """Download an image from a URL and upload it to Shopify Files via staged uploads.

    Args:
        image_url: Public URL of the image to upload.
        filename:  Desired filename (e.g. "blog-header-activation-lock.png").

    Returns:
        The Shopify CDN URL of the uploaded file.
    """
    token = _get_shopify_token()

    # --- Step 1: Download the image ---
    img_resp = requests.get(image_url, timeout=60)
    img_resp.raise_for_status()
    image_bytes = img_resp.content
    content_type = img_resp.headers.get("Content-Type", "image/png")

    # --- Step 2: Create a staged upload target ---
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

    # --- Step 3: Upload to the staged target ---
    files = {"file": (filename, image_bytes, content_type)}
    upload_resp = requests.post(
        upload_url,
        data=params,
        files=files,
        timeout=120,
    )
    upload_resp.raise_for_status()

    # --- Step 4: Create the file in Shopify ---
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

    # The CDN URL may be in .image.url for MediaImage types
    cdn_url = ""
    f = created_files[0]
    if "image" in f and f["image"]:
        cdn_url = f["image"].get("url", "")

    # If image URL isn't available yet (processing), fall back to resource URL
    if not cdn_url:
        cdn_url = resource_url

    return cdn_url
