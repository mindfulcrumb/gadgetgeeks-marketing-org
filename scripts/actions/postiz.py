"""
Postiz API wrapper for social media posting.
Docs: https://docs.postiz.com/api
"""

import json
import os
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError


POSTIZ_BASE_URL = "https://app.postiz.com/api/v1"


def _make_request(endpoint: str, method: str = "GET", data: dict = None, api_key: str = None) -> dict:
    """Make a request to the Postiz API."""
    url = f"{POSTIZ_BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key or os.environ.get('POSTIZ_API_KEY', '')}",
        "Content-Type": "application/json",
    }

    body = json.dumps(data).encode("utf-8") if data else None
    req = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise Exception(f"Postiz API error {e.code}: {error_body}")


def get_channels(api_key: str = None) -> list:
    """List all configured social media channels."""
    result = _make_request("channels", api_key=api_key)
    return result.get("channels", result if isinstance(result, list) else [])


def post_to_social(
    content: str,
    platforms: list = None,
    media_url: Optional[str] = None,
    scheduled_at: Optional[str] = None,
    api_key: str = None,
) -> dict:
    """Create and schedule a social media post via Postiz.

    Args:
        content: The post text
        platforms: List of platform names (e.g., ["twitter", "instagram"])
        media_url: Optional URL of media to attach
        scheduled_at: Optional ISO datetime for scheduling. If None, posts immediately.
        api_key: Postiz API key
    """
    data = {
        "content": content,
        "type": "post",
    }

    if scheduled_at:
        data["scheduledAt"] = scheduled_at

    if media_url:
        data["media"] = [{"url": media_url}]

    # If platforms specified, we need to get channel IDs
    if platforms:
        channels = get_channels(api_key)
        channel_ids = []
        for channel in channels:
            channel_platform = channel.get("type", "").lower()
            if channel_platform in [p.lower() for p in platforms]:
                channel_ids.append(channel.get("id"))
        if channel_ids:
            data["channelIds"] = channel_ids

    return _make_request("posts", method="POST", data=data, api_key=api_key)


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
    return result.get("posts", result if isinstance(result, list) else [])
