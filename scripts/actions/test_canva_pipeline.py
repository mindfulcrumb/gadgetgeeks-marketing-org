#!/usr/bin/env python3
"""
One-time test: Generate image via Gemini → Composite branded post with Pillow →
Upload to Shopify CDN → Push to Canva.

Tests the full pipeline end-to-end for a TikTok post about iPhone 14 100% battery health.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from image_gen import generate_image, upload_to_shopify
from canva_designer import build_branded_post

REPO_ROOT = Path(__file__).parent.parent.parent


def main():
    print("=" * 60)
    print("  PIPELINE TEST — iPhone 14 Battery Health TikTok Post")
    print(f"  Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    # --- Step 1: Generate image with Gemini ---
    print("\n[1/4] Generating image via Gemini Imagen 4...")

    prompt = (
        "Close-up of someone holding an iPhone 14 in Midnight showing the Battery Health "
        "screen at 100% Maximum Capacity. The phone screen is crisp and clearly readable. "
        "Hand belongs to a 24-year-old woman, natural nails, casual outfit sleeve visible. "
        "Background: trendy apartment with warm afternoon light, slightly blurred bokeh. "
        "Shot feels like a genuine TikTok screenshot moment — authentic, not staged. "
        "Canon EOS R5, 50mm f/1.4, shallow depth of field. Warm Kodak Portra 400 grade, "
        "golden tones. Natural skin texture. Vertical 9:16 composition for TikTok/Reels. "
        "IMG_7291.CR3 unedited RAW file."
    )

    result = generate_image(prompt, aspect_ratio="9:16")
    image_bytes = result["image_bytes"]
    mime = result["mime_type"]
    ext = "png" if "png" in mime else "jpg"
    print(f"  Image generated: {len(image_bytes):,} bytes ({mime})")

    # --- Step 2: Upload raw image to Shopify CDN ---
    print("\n[2/4] Uploading raw image to Shopify CDN...")
    filename = f"gg-test-iphone14-battery-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.{ext}"
    raw_cdn_url = upload_to_shopify(image_bytes, filename, content_type=mime)
    print(f"  Raw image CDN URL: {raw_cdn_url}")

    # --- Step 3: Create branded post (Pillow composite → Shopify CDN → Canva) ---
    print("\n[3/4] Creating branded TikTok post...")
    canva_result = build_branded_post(
        image_url=raw_cdn_url,
        platform="instagram_story",  # 1080x1920 = TikTok/Reels format
        design_type="product_spotlight",
        text_overlay={
            "headline": "100% Battery Health",
            "subline": "iPhone 14 — Inspected & Certified",
            "cta": "Shop iPhone 14",
        },
        prompt_id="test_battery_health",
    )

    # --- Results ---
    print(f"\n{'=' * 60}")
    print("  RESULTS")
    print(f"{'=' * 60}")
    print(f"  Raw image (Shopify CDN):     {raw_cdn_url}")
    print(f"  Branded post (Shopify CDN):  {canva_result.get('export_url', 'N/A')}")
    print(f"  Canva design ID:             {canva_result.get('canva_design_id', 'N/A')}")
    print(f"  Canva edit URL:              {canva_result.get('canva_edit_url', 'N/A')}")
    print(f"  Platform:                    {canva_result.get('platform', 'N/A')}")
    print(f"  Dimensions:                  {canva_result.get('dimensions', 'N/A')}")
    print(f"  Status:                      {canva_result.get('status', 'N/A')}")

    if canva_result.get("error"):
        print(f"  Error:                       {canva_result['error']}")

    # Save results
    results_path = REPO_ROOT / "departments" / "canva" / "test-result.json"
    results_path.write_text(json.dumps({
        "test": "iphone14_battery_health_tiktok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_image_url": raw_cdn_url,
        "branded_post": canva_result,
    }, indent=2), encoding="utf-8")
    print(f"\n  Results saved to: {results_path}")

    if canva_result.get("status") == "exported":
        print("\n  PIPELINE TEST PASSED")
    else:
        print("\n  PIPELINE TEST FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
