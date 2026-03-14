#!/usr/bin/env python3
"""
Direct TikTok poster — uploads ready-to-post images and schedules on Postiz.

Reads finished branded images from departments/social/ready-to-post/,
uses raw GitHub URLs (public repo) as media source, and posts to TikTok
via Postiz API with pre-written copy.

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
READY_DIR = REPO_ROOT / "departments" / "social" / "ready-to-post"
CALENDAR_PATH = REPO_ROOT / "departments" / "social" / "calendar.json"
PIPELINE_PATH = REPO_ROOT / "departments" / "canva" / "pipeline.json"

# GitHub raw URL base (public repo)
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/mindfulcrumb/gadgetgeeks-marketing-org/main"

# Pre-written TikTok copy for each post — matched to the image content
TIKTOK_POSTS = [
    {
        "image_file": "gg-iphone13-hero-tiktok.png",
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
        "image_file": "gg-iphone14-hero-tiktok.png",
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
        "image_file": "gg-iphone13-deal-tiktok.png",
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
        "image_file": "gg-iphone14-eco-tiktok.png",
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
    """Load all previously used image URLs from calendar.json."""
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
        image_file = post_info["image_file"]
        image_path = READY_DIR / image_file
        raw_url = f"{GITHUB_RAW_BASE}/departments/social/ready-to-post/{image_file}"

        # Check if burned
        if raw_url in burned or image_file in burned:
            print(f"  SKIP (already posted): {image_file}")
            continue

        # Check if file exists locally
        if not image_path.exists():
            print(f"  SKIP (file missing): {image_file}")
            continue

        # Schedule 5 min apart to avoid flooding
        schedule_time = now + timedelta(minutes=3 + (i * 30))
        schedule_str = schedule_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        print(f"\n  Posting: {image_file}")
        print(f"  Product: {post_info['product']}")
        print(f"  Schedule: {schedule_str}")
        print(f"  Media URL: {raw_url}")

        try:
            result = post_to_social(
                content=post_info["content"],
                platforms=["tiktok"],
                media_url=raw_url,
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
                "image_used": raw_url,
                "source_file": image_file,
                "canva_design_used": f"ready-to-post-{image_file}",
                "source_prompt_id": f"real_product_photo_{post_info['product'].lower().replace(' ', '_')}",
                "driven_by": "Real product photos — iPhone 13/14 bundles from gadgetgeekspro.myshopify.com",
                "posted_via": "post_ready_tiktok.py",
            })

        except Exception as e:
            print(f"  ERROR: {e}")

    # Save updated calendar
    CALENDAR_PATH.parent.mkdir(parents=True, exist_ok=True)
    CALENDAR_PATH.write_text(json.dumps(calendar, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  Calendar updated: {CALENDAR_PATH}")

    print(f"\n{'='*50}")
    print(f"  DONE: {posted_count}/{len(TIKTOK_POSTS)} posts scheduled on TikTok")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
