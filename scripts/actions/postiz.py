"""
Postiz API wrapper for social media posting.
Docs: https://docs.postiz.com/public-api
"""

import json
import os
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from datetime import datetime, timezone, timedelta


POSTIZ_BASE_URL = "https://api.postiz.com/public/v1"

# Map platform names to Postiz settings.__type values
PLATFORM_TYPE_MAP = {
    "twitter": "x",
    "x": "x",
    "instagram": "instagram",
    "facebook": "facebook",
    "linkedin": "linkedin",
    "tiktok": "tiktok",
    "reddit": "reddit",
    "threads": "threads",
    "pinterest": "pinterest",
    "youtube": "youtube",
    "bluesky": "bluesky",
    "mastodon": "mastodon",
    "telegram": "telegram",
    "discord": "discord",
}


def _make_request(endpoint: str, method: str = "GET", data: dict = None, api_key: str = None) -> dict:
    """Make a request to the Postiz public API."""
    url = f"{POSTIZ_BASE_URL}/{endpoint}"
    key = api_key or os.environ.get("POSTIZ_API_KEY", "")
    headers = {
        "Authorization": key,
        "Content-Type": "application/json",
    }

    body = json.dumps(data).encode("utf-8") if data else None
    req = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise Exception(f"Postiz API error {e.code}: {error_body}")


def get_channels(api_key: str = None) -> list:
    """List all connected integrations (social media channels).

    Returns a list of dicts with at least: id, name, identifier (platform type).
    """
    result = _make_request("integrations", api_key=api_key)
    if isinstance(result, list):
        return result
    return result.get("integrations", result.get("channels", []))


def upload_media(file_url: str, api_key: str = None) -> dict:
    """Upload media from a URL to Postiz for attachment.

    Note: For URL-based uploads, we download then re-upload.
    Returns dict with 'id' and 'path' keys.
    """
    # Postiz upload endpoint expects multipart — for URL-based media,
    # we pass the URL directly in the post payload instead.
    # This function is a placeholder for future file-based uploads.
    return {"id": None, "path": file_url}


def post_to_social(
    content: str,
    platforms: list = None,
    media_url: Optional[str] = None,
    scheduled_at: Optional[str] = None,
    api_key: str = None,
) -> dict:
    """Create and schedule a social media post via Postiz.

    Args:
        content: The post text.
        platforms: List of platform names (e.g., ["twitter", "instagram"]).
                   If None, posts to all connected integrations.
        media_url: Optional URL of media to attach.
        scheduled_at: Optional ISO datetime for scheduling. If None, posts now.
        api_key: Postiz API key.
    """
    # Step 1: Get connected integrations
    integrations = get_channels(api_key)
    if not integrations:
        raise Exception("No connected integrations found in Postiz. Connect accounts at app.postiz.com first.")

    # Step 2: Filter integrations by requested platforms
    target_integrations = []
    if platforms:
        platform_lower = [p.lower() for p in platforms]
        for integ in integrations:
            integ_type = (
                integ.get("identifier", "")
                or integ.get("type", "")
                or integ.get("providerIdentifier", "")
            ).lower()
            # Match by identifier or name
            if integ_type in platform_lower or integ.get("name", "").lower() in platform_lower:
                target_integrations.append(integ)
            # Also match mapped names (e.g., "twitter" -> "x")
            for pname in platform_lower:
                mapped = PLATFORM_TYPE_MAP.get(pname, pname)
                if integ_type == mapped:
                    if integ not in target_integrations:
                        target_integrations.append(integ)
    else:
        target_integrations = integrations

    if not target_integrations:
        # Fall back to ALL connected integrations if none of the requested ones match
        available = [i.get("identifier", i.get("type", "?")) for i in integrations]
        print(f"  Postiz: requested platforms {platforms} not found. Falling back to available: {available}")
        target_integrations = integrations

    if not target_integrations:
        raise Exception("No integrations connected in Postiz at all.")

    # Step 3: Build image attachment if media_url provided
    image_payload = []
    if media_url:
        image_payload = [{"id": "media_0", "path": media_url}]

    # Step 4: Build per-integration post objects
    posts = []
    for integ in target_integrations:
        integ_type = (
            integ.get("identifier", "")
            or integ.get("type", "")
            or integ.get("providerIdentifier", "")
        ).lower()
        settings_type = PLATFORM_TYPE_MAP.get(integ_type, integ_type)

        post_obj = {
            "integration": {"id": integ["id"]},
            "value": [
                {
                    "content": content,
                    "image": image_payload,
                }
            ],
            "settings": {
                "__type": settings_type,
            },
        }
        posts.append(post_obj)

    # Step 5: Build the top-level payload
    payload = {
        "type": "schedule" if scheduled_at else "now",
        "shortLink": False,
        "tags": [],
        "posts": posts,
    }

    if scheduled_at:
        payload["date"] = scheduled_at
    else:
        # Schedule 2 minutes from now to avoid timing edge cases
        future = datetime.now(timezone.utc) + timedelta(minutes=2)
        payload["date"] = future.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # Step 6: Create the post
    result = _make_request("posts", method="POST", data=payload, api_key=api_key)
    platforms_str = ", ".join(
        integ.get("identifier", integ.get("type", "?"))
        for integ in target_integrations
    )
    print(f"  Postiz: scheduled to {platforms_str}")
    return result


def list_posts(start_date: str = None, end_date: str = None, api_key: str = None) -> list:
    """List posts, optionally filtered by date range."""
    endpoint = "posts"
    params = []
    if start_date:
        params.append(f"startDate={start_date}")
    if end_date:
        params.append(f"endDate={end_date}")
    if params:
        endpoint += "?" + "&".join(params)

    result = _make_request(endpoint, api_key=api_key)
    if isinstance(result, list):
        return result
    return result.get("posts", [])


def find_next_slot(integration_id: str, api_key: str = None) -> dict:
    """Find the next available posting slot for a channel."""
    return _make_request(f"find-slot/{integration_id}", api_key=api_key)
