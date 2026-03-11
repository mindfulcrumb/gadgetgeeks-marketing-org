"""
Resend API wrapper for email sending.
Docs: https://resend.com/docs/api-reference
"""

import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError


RESEND_BASE_URL = "https://api.resend.com"


def send_email(
    to: str | list,
    subject: str,
    html_body: str,
    from_email: str = "Gadget Geeks Pro <noreply@gadgetgeekspro.com>",
    reply_to: str = None,
    api_key: str = None,
) -> dict:
    """Send an email via the Resend API.

    Args:
        to: Email address or list of addresses
        subject: Email subject line
        html_body: HTML email body
        from_email: From address (must be verified in Resend)
        reply_to: Optional reply-to address
        api_key: Resend API key
    """
    key = api_key or os.environ.get("RESEND_API_KEY", "")
    if not key:
        raise Exception("RESEND_API_KEY not set")

    if isinstance(to, str):
        to = [to]

    data = {
        "from": from_email,
        "to": to,
        "subject": subject,
        "html": html_body,
    }

    if reply_to:
        data["reply_to"] = reply_to

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    body = json.dumps(data).encode("utf-8")
    req = Request(f"{RESEND_BASE_URL}/emails", data=body, headers=headers, method="POST")

    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise Exception(f"Resend API error {e.code}: {error_body}")
