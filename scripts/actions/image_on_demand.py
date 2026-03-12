#!/usr/bin/env python3
"""
On-demand image generation — processes requests from Telegram /image command.

Flow:
1. Read image-queue.json for pending requests
2. Use Claude to turn the brief into a proper image prompt (following LENS rules)
3. Generate image with Gemini Imagen 4
4. Brand with Pillow (text overlay, gradient, CTA)
5. Upload to Shopify CDN + Canva
6. Send results back to Telegram with approval links
7. Move request from pending → completed
"""

import json
import os
import sys
import requests
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from image_gen import generate_image, upload_to_shopify
from canva_designer import build_branded_post

REPO_ROOT = Path(__file__).parent.parent.parent
QUEUE_PATH = REPO_ROOT / "departments" / "canva" / "image-queue.json"


def brief_to_prompt(brief: str) -> dict:
    """Use Claude to convert a brief into a proper LENS-style image prompt.

    Returns:
        {
            "prompt": str,
            "negative_prompt": str,
            "aspect_ratio": str,
            "platform": str,
            "design_type": str,
            "text_overlay": {"headline": str, "subline": str, "cta": str},
        }
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        # Fallback: build a basic prompt from the brief
        return _basic_prompt(brief)

    system_msg = """You are LENS, the Visual Director for Gadget Geeks Pro (refurbished phone store).
Convert the user's brief into a photorealistic image prompt.

CRITICAL RULES:
- The image must look like a REAL PHOTO taken from a cellphone, not AI-generated
- NEVER include specific phone UI/screens (battery health, settings, apps). Screen must be OFF or show simple wallpaper
- Include: real camera (Canon EOS R5, Leica M11, etc.), lens, film stock, skin realism stack for people
- End with IMG_XXXX.CR3 untitled unedited RAW file
- Include negative prompt: NO AI artifacts, NO fake UI, NO plastic skin, NO watermark
- Max 800 characters for the prompt

Return ONLY valid JSON (no markdown, no explanation):
{
  "prompt": "the full image prompt",
  "negative_prompt": "NO AI artifacts, NO fake UI...",
  "aspect_ratio": "9:16 or 1:1 or 16:9",
  "platform": "tiktok or instagram or twitter or facebook",
  "design_type": "product_spotlight or lifestyle or deal_urgency or sustainability",
  "text_overlay": {
    "headline": "short headline (max 5 words)",
    "subline": "one line subtext",
    "cta": "Shop Now or Check Price etc"
  }
}"""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "system": system_msg,
                "messages": [{"role": "user", "content": f"Brief: {brief}"}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"].strip()

        # Parse JSON from response (handle potential markdown wrapping)
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as e:
        print(f"  Claude prompt generation failed ({e}), using basic prompt")
        return _basic_prompt(brief)


def _basic_prompt(brief: str) -> dict:
    """Fallback: build a basic prompt from the brief without Claude."""
    # Detect platform from brief
    brief_lower = brief.lower()
    if "tiktok" in brief_lower or "reel" in brief_lower:
        aspect = "9:16"
        platform = "tiktok"
    elif "story" in brief_lower:
        aspect = "9:16"
        platform = "instagram_story"
    elif "twitter" in brief_lower or "x " in brief_lower:
        aspect = "16:9"
        platform = "twitter"
    else:
        aspect = "1:1"
        platform = "instagram"

    # Detect design type
    if "deal" in brief_lower or "sale" in brief_lower or "urgency" in brief_lower:
        design_type = "deal_urgency"
    elif "eco" in brief_lower or "sustain" in brief_lower:
        design_type = "sustainability"
    else:
        design_type = "product_spotlight"

    # Extract phone model if mentioned
    phone = ""
    for model in ["iPhone 16", "iPhone 15", "iPhone 14", "iPhone 13", "Galaxy S25", "Galaxy S24", "Pixel 9"]:
        if model.lower() in brief_lower:
            phone = model
            break
    phone = phone or "iPhone 14"

    prompt = (
        f"Candid lifestyle photo: young person holding a {phone} in pristine like-new condition, "
        f"screen off/dark. Natural environment, warm lighting. The person looks relaxed and genuine — "
        f"this should look like a real photo someone posted, not staged. "
        f"Natural skin with visible pores, subsurface scattering, natural facial asymmetry. "
        f"Canon EOS R5, 50mm f/1.4, shallow depth of field. Kodak Portra 400, warm grade. "
        f"IMG_{hash(brief) % 10000:04d}.CR3 untitled unedited RAW file."
    )

    # Extract a headline from the brief
    headline_words = [w for w in brief.split() if w[0].isupper() or w.isdigit()] if brief else []
    headline = " ".join(headline_words[:5]) or phone

    return {
        "prompt": prompt,
        "negative_prompt": "NO AI artifacts, NO fake UI, NO plastic skin, NO watermark, NO text on screen",
        "aspect_ratio": aspect,
        "platform": platform,
        "design_type": design_type,
        "text_overlay": {
            "headline": headline,
            "subline": f"{phone} — Inspected & Certified",
            "cta": "Shop Now",
        },
    }


def send_telegram(chat_id: str, text: str, image_url: str = None):
    """Send a message (optionally with image) to Telegram."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        print("  No TELEGRAM_BOT_TOKEN — skipping notification")
        return

    if image_url:
        # Send photo with caption
        resp = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendPhoto",
            json={
                "chat_id": chat_id,
                "photo": image_url,
                "caption": text[:1024],
                "parse_mode": "HTML",
            },
            timeout=15,
        )
    else:
        resp = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text[:4096],
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
            timeout=15,
        )

    if resp.status_code != 200:
        print(f"  Telegram send failed: {resp.status_code} {resp.text[:200]}")


def process_queue():
    """Process all pending image requests from the queue."""
    if not QUEUE_PATH.exists():
        print("No image queue file found")
        return

    queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    pending = queue.get("pending", [])

    if not pending:
        print("No pending image requests")
        return

    print(f"Processing {len(pending)} pending image request(s)...")

    for request in pending[:5]:  # Max 5 per run
        request_id = request.get("id", "unknown")
        brief = request.get("brief", "")
        chat_id = request.get("chat_id", "")

        print(f"\n--- Processing: {request_id} ---")
        print(f"  Brief: {brief}")

        try:
            # 1. Convert brief to prompt
            print("  [1/4] Converting brief to image prompt...")
            prompt_data = brief_to_prompt(brief)
            print(f"  Platform: {prompt_data['platform']}, Type: {prompt_data['design_type']}")

            # 2. Generate image
            print("  [2/4] Generating image via Gemini...")
            result = generate_image(prompt_data["prompt"], aspect_ratio=prompt_data["aspect_ratio"])
            image_bytes = result["image_bytes"]
            mime = result["mime_type"]
            ext = "png" if "png" in mime else "jpg"
            print(f"  Generated: {len(image_bytes):,} bytes")

            # 3. Upload raw image to Shopify CDN
            print("  [3/4] Uploading to Shopify CDN...")
            now_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            raw_filename = f"gg-ondemand-{request_id}-{now_str}.{ext}"
            raw_cdn_url = upload_to_shopify(image_bytes, raw_filename, content_type=mime)
            print(f"  Raw CDN: {raw_cdn_url}")

            # 4. Create branded post
            print("  [4/4] Creating branded post...")
            branded_result = build_branded_post(
                image_url=raw_cdn_url,
                platform=prompt_data.get("platform", "instagram"),
                design_type=prompt_data.get("design_type", "product_spotlight"),
                text_overlay=prompt_data.get("text_overlay", {}),
                prompt_id=request_id,
            )

            # Update request
            request["status"] = "completed"
            request["completed_at"] = datetime.now(timezone.utc).isoformat()
            request["raw_image_url"] = raw_cdn_url
            request["branded_post_url"] = branded_result.get("export_url", "")
            request["canva_edit_url"] = branded_result.get("canva_edit_url", "")
            request["canva_design_id"] = branded_result.get("canva_design_id", "")

            # Send results to Telegram
            if chat_id:
                branded_url = branded_result.get("export_url", "")
                canva_url = branded_result.get("canva_edit_url", "")

                msg = (
                    f"\u{1F3A8} <b>IMAGE READY</b>\n\n"
                    f"<b>Brief:</b> <i>{brief[:100]}</i>\n\n"
                    f"\u{1F5BC}\uFE0F <b>Raw image:</b>\n{raw_cdn_url}\n\n"
                    f"\u2728 <b>Branded post:</b>\n{branded_url}\n\n"
                )
                if canva_url:
                    msg += f"\u{270F}\uFE0F <b>Edit in Canva:</b>\n{canva_url}\n\n"
                msg += f"<b>ID:</b> <code>{request_id}</code>"

                # Send branded image as photo
                send_telegram(chat_id, msg, image_url=branded_url or raw_cdn_url)

            print(f"  DONE: {request_id}")

        except Exception as e:
            print(f"  ERROR: {e}")
            request["status"] = "error"
            request["error"] = str(e)[:300]
            request["completed_at"] = datetime.now(timezone.utc).isoformat()

            if chat_id:
                send_telegram(
                    chat_id,
                    f"\u274C <b>Image generation failed</b>\n\n"
                    f"<b>Brief:</b> <i>{brief[:100]}</i>\n"
                    f"<b>Error:</b> {str(e)[:200]}\n\n"
                    f"Try again with /image",
                )

    # Move completed from pending to completed
    still_pending = [r for r in pending if r.get("status") == "pending"]
    done = [r for r in pending if r.get("status") != "pending"]
    queue["pending"] = still_pending
    queue["completed"] = (queue.get("completed", []) + done)[-50:]  # Keep last 50

    QUEUE_PATH.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nQueue updated: {len(done)} completed, {len(still_pending)} still pending")


if __name__ == "__main__":
    print("=" * 60)
    print("  IMAGE ON-DEMAND — TELEGRAM QUEUE PROCESSOR")
    print(f"  Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)
    process_queue()
