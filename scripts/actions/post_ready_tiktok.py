#!/usr/bin/env python3
"""
Direct TikTok poster — uses Canva-designed images on Shopify CDN and schedules on Postiz.

Images: Canva exports uploaded to Shopify CDN (permanent URLs).
Source photos: gc001-gc004 from Shopify Files (gadgetgeekspro.myshopify.com).

Usage:
  python scripts/actions/post_ready_tiktok.py

Requires:
  POSTIZ_API_KEY env var
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add parent dir for imports
sys.path.insert(0, str(Path(__file__).parent))
from postiz import post_to_social

REPO_ROOT = Path(__file__).parent.parent.parent
CALENDAR_PATH = REPO_ROOT / "departments" / "social" / "calendar.json"

# Canva-designed TikTok posts with permanent Shopify CDN URLs
# Source: gc001-gc004 from Shopify Files → Canva design → Export PNG → Shopify CDN
TIKTOK_POSTS = [
    {
        "id": "canva_design1_iphone_flatlat",
        "canva_design_id": "DAHD7jU4OMw",
        "cdn_url": "https://cdn.shopify.com/s/files/1/0664/1664/0251/files/gg-tiktok-design1.png?v=1773498404",
        "product": "iPhone 13",
        "content": (
            "iPhone 13 bundle for under $300?\n\n"
            "Phone + MagSafe case + screen protector + camera lens protector + charger + cable.\n\n"
            "65-point inspection. 90-day warranty. All 6 colors in stock.\n\n"
            "Why pay $599 retail when you don't have to?\n\n"
            "Link in bio\n\n"
            "#refurbishediphone #iphone13 #phonedeals #budgetphone #fyp"
        ),
        "design_type": "product_hero",
    },
    {
        "id": "canva_design2_iphone_hero",
        "canva_design_id": "DAHD7nNxlN4",
        "cdn_url": "https://cdn.shopify.com/s/files/1/0664/1664/0251/files/gg-tiktok-design2.png?v=1773498404",
        "product": "iPhone 14",
        "content": (
            "iPhone 14 bundle — everything you need in one box\n\n"
            "MagSafe case. Screen protector. Camera guard. Charger. Cable.\n\n"
            "Tested 65 points. Looks brand new. Costs 40% less.\n\n"
            "Your wallet's gonna thank you\n\n"
            "Link in bio\n\n"
            "#iphone14 #refurbished #techdeals #savemoney #foryou"
        ),
        "design_type": "product_hero",
    },
    {
        "id": "canva_design3_iphone_deal",
        "canva_design_id": "DAHD7ox7jyY",
        "cdn_url": "https://cdn.shopify.com/s/files/1/0664/1664/0251/files/gg-tiktok-design3.png?v=1773498404",
        "product": "iPhone 13",
        "content": (
            "This iPhone 13 deal won't last\n\n"
            "Full bundle — phone, case, protectors, charger — for what most people pay for JUST the phone\n\n"
            "Every unit passes our 65-point inspection\n"
            "90-day warranty included\n"
            "Free shipping\n\n"
            "Save this before it sells out\n\n"
            "#iphone13deal #refurbishedphones #gadgetgeekspro #phoneaccessories #fyp"
        ),
        "design_type": "deal_urgency",
    },
    {
        "id": "canva_design4_iphone_ugc",
        "canva_design_id": "DAHD7pxTtSI",
        "cdn_url": "https://cdn.shopify.com/s/files/1/0664/1664/0251/files/gg-tiktok-design4.png?v=1773498404",
        "product": "iPhone 14",
        "content": (
            "Buying refurbished = 1 less phone in a landfill\n\n"
            "This iPhone 14 got a second life. Still runs like new.\n\n"
            "65-point tested. 90-day warranty. Full bundle included.\n\n"
            "Good for your wallet. Good for the planet.\n\n"
            "Follow for more sustainable tech\n\n"
            "#sustainabletech #refurbished #iphone14 #ecofriendly #foryou"
        ),
        "design_type": "sustainability",
    },
]


def get_burned_images():
    """Load all previously used image URLs and design IDs from calendar.json."""
    burned = set()
    if CALENDAR_PATH.exists():
        try:
            cal = json.loads(CALENDAR_PATH.read_text(encoding="utf-8"))
            entries = cal if isinstance(cal, list) else cal.get("posts", cal.get("entries", []))
            for entry in entries:
                if isinstance(entry, dict):
                    img = entry.get("image_used", "")
                    if img:
                        burned.add(img)
                    design_id = entry.get("canva_design_used", "")
                    if design_id:
                        burned.add(design_id)
        except Exception:
            pass
    return burned


def main():
    api_key = os.environ.get("POSTIZ_API_KEY")
    if not api_key:
        print("ERROR: POSTIZ_API_KEY not set")
        sys.exit(1)

    burned = get_burned_images()
    print(f"Burned images from calendar: {len(burned)}")

    # Load calendar for appending
    if CALENDAR_PATH.exists():
        try:
            calendar = json.loads(CALENDAR_PATH.read_text(encoding="utf-8"))
        except Exception:
            calendar = {"posts": []}
    else:
        calendar = {"posts": []}

    # Normalize calendar structure
    if isinstance(calendar, list):
        calendar = {"posts": calendar}
    if "posts" not in calendar:
        calendar["posts"] = calendar.get("entries", [])

    posted_count = 0
    now = datetime.now(timezone.utc)

    for i, post_info in enumerate(TIKTOK_POSTS):
        cdn_url = post_info["cdn_url"]
        canva_id = post_info["canva_design_id"]

        # Check if burned
        if cdn_url in burned or canva_id in burned:
            print(f"  SKIP (already posted): {post_info['id']}")
            continue

        # Schedule 30 min apart
        schedule_time = now + timedelta(minutes=3 + (i * 30))
        schedule_str = schedule_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        print(f"\n  Posting: {post_info['id']}")
        print(f"  Product: {post_info['product']}")
        print(f"  Schedule: {schedule_str}")
        print(f"  CDN URL: {cdn_url}")

        try:
            result = post_to_social(
                content=post_info["content"],
                platforms=["tiktok"],
                media_url=cdn_url,
                scheduled_at=schedule_str,
                api_key=api_key,
            )
            print(f"  SUCCESS: Posted to TikTok")
            posted_count += 1

            # Log to calendar
            calendar["posts"].append({
                "date": now.strftime("%Y-%m-%d"),
                "time": schedule_str,
                "platform": "tiktok",
                "content_type": post_info["design_type"],
                "product": post_info["product"],
                "content_preview": post_info["content"][:80],
                "image_used": cdn_url,
                "canva_design_used": canva_id,
                "source": "canva_export_shopify_cdn",
                "driven_by": "Real product photos gc001-gc004 from gadgetgeekspro.myshopify.com → Canva designed → Shopify CDN",
                "posted_via": "post_ready_tiktok.py",
            })

        except Exception as e:
            print(f"  ERROR: {e}")

    # Update postiz call counters
    calendar["postiz_calls_used"] = calendar.get("postiz_calls_used", 0) + posted_count
    calendar["postiz_calls_remaining"] = max(0, calendar.get("postiz_calls_remaining", 15) - posted_count)

    # Save updated calendar
    CALENDAR_PATH.parent.mkdir(parents=True, exist_ok=True)
    CALENDAR_PATH.write_text(json.dumps(calendar, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  Calendar updated: {CALENDAR_PATH}")

    print(f"\n{'='*50}")
    print(f"  DONE: {posted_count}/{len(TIKTOK_POSTS)} posts scheduled on TikTok")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
