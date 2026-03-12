"""
Canva post designer for GadgetGeeks Marketing Organization.

Uses the Canva Connect API to create branded social media posts
from AI-generated images. Takes raw images from the image pipeline
and produces finished, platform-ready designs.
"""

import json
import os
import requests
import time
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CANVA_API_BASE = "https://api.canva.com/rest/v1"
REPO_ROOT = Path(__file__).parent.parent.parent


def _fetch_token_from_worker() -> str:
    """Fetch a fresh Canva access token from the Cloudflare Worker."""
    worker_url = os.environ.get("CANVA_TOKEN_WORKER_URL", "")
    worker_secret = os.environ.get("WORKER_API_SECRET", "")
    if not worker_url or not worker_secret:
        return ""
    try:
        resp = requests.get(
            f"{worker_url}/canva/token",
            headers={"X-Worker-Secret": worker_secret},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                return data["access_token"]
        print(f"[canva] Worker token fetch failed: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        print(f"[canva] Worker token fetch error: {e}")
    return ""


def _canva_headers() -> dict:
    """Build authorization headers for Canva Connect API."""
    # Try worker first (auto-refresh), fall back to env var
    token = _fetch_token_from_worker() or os.environ.get("CANVA_ACCESS_TOKEN", "")
    if not token:
        raise ValueError(
            "No Canva token available. Set CANVA_TOKEN_WORKER_URL + WORKER_API_SECRET "
            "or CANVA_ACCESS_TOKEN directly."
        )
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Canva API Operations
# ---------------------------------------------------------------------------

def create_design(title: str, width: int, height: int) -> dict:
    """Create a new blank Canva design.

    Args:
        title:  Design title (visible in Canva dashboard).
        width:  Width in pixels.
        height: Height in pixels.

    Returns:
        {"design_id": str, "edit_url": str, "title": str}
    """
    resp = requests.post(
        f"{CANVA_API_BASE}/designs",
        headers=_canva_headers(),
        json={
            "design_type": {
                "type": "custom_size",
                "width": width,
                "height": height,
            },
            "title": title,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json().get("design", {})
    return {
        "design_id": data.get("id", ""),
        "edit_url": data.get("urls", {}).get("edit_url", ""),
        "title": data.get("title", title),
    }


def upload_asset(image_url: str, title: str = "Generated Image") -> dict:
    """Upload an image from URL to Canva as a reusable asset.

    Args:
        image_url: Public URL of the image to upload.
        title:     Asset title.

    Returns:
        {"asset_id": str, "thumbnail_url": str}
    """
    # Step 1: Start the upload job
    resp = requests.post(
        f"{CANVA_API_BASE}/asset-uploads",
        headers=_canva_headers(),
        json={
            "name_base64": __import__("base64").b64encode(title.encode()).decode(),
            "url": image_url,
        },
        timeout=30,
    )
    resp.raise_for_status()
    job = resp.json().get("job", {})
    job_id = job.get("id", "")

    if not job_id:
        # Direct asset return (some API versions)
        asset = resp.json().get("asset", {})
        return {
            "asset_id": asset.get("id", ""),
            "thumbnail_url": asset.get("thumbnail", {}).get("url", ""),
        }

    # Step 2: Poll for completion
    for _ in range(20):
        time.sleep(3)
        status_resp = requests.get(
            f"{CANVA_API_BASE}/asset-uploads/{job_id}",
            headers=_canva_headers(),
            timeout=15,
        )
        status_resp.raise_for_status()
        status_data = status_resp.json().get("job", {})
        if status_data.get("status") == "success":
            asset = status_data.get("asset", {})
            return {
                "asset_id": asset.get("id", ""),
                "thumbnail_url": asset.get("thumbnail", {}).get("url", ""),
            }
        if status_data.get("status") == "failed":
            raise RuntimeError(f"Asset upload failed: {status_data.get('error', {})}")

    raise RuntimeError("Asset upload timed out after 60 seconds")


def start_editing(design_id: str) -> str:
    """Start an editing transaction on a design.

    Returns:
        Transaction ID (used for subsequent editing operations).
    """
    resp = requests.post(
        f"{CANVA_API_BASE}/designs/{design_id}/editing/transactions",
        headers=_canva_headers(),
        json={},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("transaction", {}).get("id", "")


def add_elements(design_id: str, transaction_id: str, elements: list) -> dict:
    """Add elements (text, images, shapes) to a design within an editing transaction.

    Args:
        design_id:      The Canva design ID.
        transaction_id: Active editing transaction ID.
        elements:       List of element definitions.

    Returns:
        API response dict.
    """
    resp = requests.post(
        f"{CANVA_API_BASE}/designs/{design_id}/editing/transactions/{transaction_id}/elements",
        headers=_canva_headers(),
        json={"elements": elements},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def commit_editing(design_id: str, transaction_id: str) -> dict:
    """Commit an editing transaction, finalizing all changes.

    Returns:
        API response dict.
    """
    resp = requests.post(
        f"{CANVA_API_BASE}/designs/{design_id}/editing/transactions/{transaction_id}/commit",
        headers=_canva_headers(),
        json={},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def export_design(design_id: str, format: str = "png") -> str:
    """Export a finished design as PNG/JPG.

    Args:
        design_id: The Canva design ID.
        format:    "png" or "jpg".

    Returns:
        Export download URL.
    """
    # Step 1: Start export job
    resp = requests.post(
        f"{CANVA_API_BASE}/designs/{design_id}/exports",
        headers=_canva_headers(),
        json={
            "format": {"type": format},
        },
        timeout=15,
    )
    resp.raise_for_status()
    job = resp.json().get("job", {})
    job_id = job.get("id", "")

    if not job_id:
        # Direct URL return
        return resp.json().get("export", {}).get("urls", [{}])[0].get("url", "")

    # Step 2: Poll for completion
    for _ in range(30):
        time.sleep(2)
        status_resp = requests.get(
            f"{CANVA_API_BASE}/designs/{design_id}/exports/{job_id}",
            headers=_canva_headers(),
            timeout=15,
        )
        status_resp.raise_for_status()
        status_data = status_resp.json().get("job", {})

        if status_data.get("status") == "success":
            urls = status_data.get("urls", [])
            if urls:
                return urls[0].get("url", "")
            return ""

        if status_data.get("status") == "failed":
            raise RuntimeError(f"Export failed: {status_data.get('error', {})}")

    raise RuntimeError("Export timed out after 60 seconds")


# ---------------------------------------------------------------------------
# Design Builder — creates a complete branded post
# ---------------------------------------------------------------------------

def build_branded_post(
    image_url: str,
    platform: str,
    design_type: str,
    text_overlay: dict,
    prompt_id: str,
) -> dict:
    """Build a complete branded social media post in Canva.

    Args:
        image_url:    CDN URL of the AI-generated image.
        platform:     Target platform (instagram, twitter, facebook, etc.).
        design_type:  One of: product_spotlight, deal_urgency, lifestyle, sustainability, comparison.
        text_overlay: Dict with keys: headline, subline, cta.
        prompt_id:    Source prompt ID for traceability.

    Returns:
        {
            "canva_design_id": str,
            "canva_edit_url": str,
            "export_url": str,
            "platform": str,
            "dimensions": str,
            "status": str,
        }
    """
    # Platform dimensions
    DIMENSIONS = {
        "instagram": (1080, 1080),
        "instagram_story": (1080, 1920),
        "twitter": (1600, 900),
        "facebook": (1200, 630),
        "linkedin": (1200, 627),
        "pinterest": (1000, 1500),
    }

    width, height = DIMENSIONS.get(platform, (1080, 1080))
    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    title = f"GGP_{platform}_{design_type}_{now}"

    try:
        # 1. Create the design
        design = create_design(title, width, height)
        design_id = design["design_id"]

        # 2. Upload the AI-generated image as an asset
        asset = upload_asset(image_url, title=f"bg_{prompt_id}")

        # 3. Start editing transaction
        txn_id = start_editing(design_id)

        # 4. Build element list
        elements = _build_elements(
            asset_id=asset["asset_id"],
            width=width,
            height=height,
            design_type=design_type,
            text_overlay=text_overlay,
        )

        # 5. Add elements
        add_elements(design_id, txn_id, elements)

        # 6. Commit the editing transaction
        commit_editing(design_id, txn_id)

        # 7. Export the final design
        export_url = export_design(design_id, format="png")

        return {
            "canva_design_id": design_id,
            "canva_edit_url": design["edit_url"],
            "export_url": export_url,
            "platform": platform,
            "dimensions": f"{width}x{height}",
            "status": "exported",
        }

    except Exception as e:
        print(f"  ERROR building Canva design for {prompt_id}: {e}")
        return {
            "canva_design_id": "",
            "canva_edit_url": "",
            "export_url": "",
            "platform": platform,
            "dimensions": f"{width}x{height}",
            "status": "error",
            "error": str(e)[:300],
        }


def _build_elements(
    asset_id: str,
    width: int,
    height: int,
    design_type: str,
    text_overlay: dict,
) -> list:
    """Build the element list for a branded post.

    Returns a list of Canva element definitions: background image,
    text blocks, gradient overlay, logo placement.
    """
    elements = []

    # 1. Background image (full bleed)
    elements.append({
        "type": "image",
        "asset_id": asset_id,
        "position": {"x": 0, "y": 0},
        "size": {"width": width, "height": height},
    })

    # 2. Gradient overlay for text readability (bottom third)
    if design_type in ("product_spotlight", "deal_urgency", "comparison"):
        elements.append({
            "type": "shape",
            "shape_type": "rectangle",
            "position": {"x": 0, "y": int(height * 0.6)},
            "size": {"width": width, "height": int(height * 0.4)},
            "fill": {
                "type": "gradient",
                "stops": [
                    {"color": "#00000000", "position": 0},
                    {"color": "#000000CC", "position": 100},
                ],
            },
        })

    # 3. Text overlays
    headline = text_overlay.get("headline", "")
    subline = text_overlay.get("subline", "")
    cta = text_overlay.get("cta", "")

    if headline:
        # Headline — large, bold, bottom area
        font_size = 56 if width >= 1200 else 44 if width >= 1080 else 36
        elements.append({
            "type": "text",
            "content": headline,
            "position": {"x": int(width * 0.05), "y": int(height * 0.65)},
            "size": {"width": int(width * 0.9), "height": int(font_size * 1.5)},
            "font": {
                "family": "Plus Jakarta Sans",
                "weight": "bold",
                "size": font_size,
            },
            "color": "#FFFFFF",
            "text_align": "left",
        })

    if subline:
        # Subline — medium, below headline
        sub_size = 32 if width >= 1200 else 28 if width >= 1080 else 24
        elements.append({
            "type": "text",
            "content": subline,
            "position": {"x": int(width * 0.05), "y": int(height * 0.78)},
            "size": {"width": int(width * 0.9), "height": int(sub_size * 1.5)},
            "font": {
                "family": "Inter",
                "weight": "regular",
                "size": sub_size,
            },
            "color": "#FFFFFF",
            "text_align": "left",
        })

    if cta:
        # CTA badge — brand pink, bottom right
        cta_size = 28 if width >= 1200 else 24
        badge_w = min(len(cta) * cta_size * 0.6, width * 0.5)
        elements.append({
            "type": "shape",
            "shape_type": "rounded_rectangle",
            "position": {
                "x": int(width * 0.95 - badge_w),
                "y": int(height * 0.88),
            },
            "size": {"width": int(badge_w), "height": int(cta_size * 2)},
            "fill": {"type": "solid", "color": "#C72F8F"},
            "corner_radius": 8,
        })
        elements.append({
            "type": "text",
            "content": cta,
            "position": {
                "x": int(width * 0.95 - badge_w + 16),
                "y": int(height * 0.88 + cta_size * 0.4),
            },
            "size": {"width": int(badge_w - 32), "height": int(cta_size * 1.4)},
            "font": {
                "family": "Plus Jakarta Sans",
                "weight": "bold",
                "size": cta_size,
            },
            "color": "#FFFFFF",
            "text_align": "center",
        })

    # 4. Logo — bottom left, small
    # (Uses brand text since we can't upload a logo asset in every run)
    logo_size = 16 if width >= 1200 else 14
    elements.append({
        "type": "text",
        "content": "GADGET GEEKS PRO",
        "position": {"x": int(width * 0.03), "y": int(height * 0.94)},
        "size": {"width": int(width * 0.35), "height": int(logo_size * 1.8)},
        "font": {
            "family": "Plus Jakarta Sans",
            "weight": "bold",
            "size": logo_size,
        },
        "color": "#FFFFFF80",
        "text_align": "left",
    })

    return elements


# ---------------------------------------------------------------------------
# Batch processor — processes all pending images
# ---------------------------------------------------------------------------

def process_batch() -> dict:
    """Process all generated images that haven't been designed yet.

    Reads image-prompts.json, creates Canva designs for each image
    with generated_url, updates both pipeline files.

    Returns:
        {"success": int, "failed": int, "skipped": int, "designs": list}
    """
    prompts_path = REPO_ROOT / "departments" / "social" / "image-prompts.json"
    pipeline_path = REPO_ROOT / "departments" / "canva" / "pipeline.json"

    if not prompts_path.exists():
        print("ERROR: image-prompts.json not found")
        return {"success": 0, "failed": 0, "skipped": 0, "designs": []}

    prompts_data = json.loads(prompts_path.read_text(encoding="utf-8"))
    pipeline_data = json.loads(pipeline_path.read_text(encoding="utf-8"))

    results = {"success": 0, "failed": 0, "skipped": 0, "designs": []}

    # Platform rotation for variety
    platform_cycle = [
        "instagram", "twitter", "instagram", "instagram_story",
        "facebook", "instagram", "twitter", "linkedin",
        "pinterest", "instagram_story",
    ]
    platform_idx = 0

    # Process each folder's prompts
    folders = prompts_data.get("folders", {})
    for folder_name, folder_data in folders.items():
        for prompt_item in folder_data.get("prompts", []):
            # Skip if no generated image
            if not prompt_item.get("generated_url"):
                results["skipped"] += 1
                continue

            # Skip if already designed
            if prompt_item.get("canva_design_status") == "designed":
                results["skipped"] += 1
                continue

            # Determine design type from folder
            design_type_map = {
                "product_hero": "product_spotlight",
                "lifestyle": "lifestyle",
                "sustainability": "sustainability",
                "deal_urgency": "deal_urgency",
                "comparison": "comparison",
            }
            design_type = design_type_map.get(folder_name, "lifestyle")

            # Pick platform
            platform = prompt_item.get("platform", platform_cycle[platform_idx % len(platform_cycle)])
            platform_idx += 1

            # Build text overlay from prompt context
            text_overlay = _build_text_overlay(prompt_item, design_type)

            print(f"  Designing: {prompt_item.get('id', '?')} → {platform} {design_type}")

            # Build the Canva design
            result = build_branded_post(
                image_url=prompt_item["generated_url"],
                platform=platform,
                design_type=design_type,
                text_overlay=text_overlay,
                prompt_id=prompt_item.get("id", "unknown"),
            )

            now = datetime.now(timezone.utc).isoformat()

            if result["status"] == "exported":
                results["success"] += 1
                prompt_item["canva_design_status"] = "designed"
                prompt_item["canva_design_id"] = result["canva_design_id"]
                prompt_item["canva_export_url"] = result["export_url"]
            else:
                results["failed"] += 1
                prompt_item["canva_design_status"] = "error"
                prompt_item["canva_design_error"] = result.get("error", "Unknown error")

            # Add to pipeline
            design_entry = {
                "id": f"canva_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{platform_idx:03d}",
                "source_prompt_id": prompt_item.get("id", ""),
                "source_image_url": prompt_item.get("generated_url", ""),
                "canva_design_id": result.get("canva_design_id", ""),
                "canva_edit_url": result.get("canva_edit_url", ""),
                "export_url": result.get("export_url", ""),
                "platform": platform,
                "dimensions": result.get("dimensions", ""),
                "design_type": design_type,
                "text_overlay": text_overlay,
                "status": result["status"],
                "created_at": now,
            }
            if result.get("error"):
                design_entry["error"] = result["error"]

            pipeline_data["designs"].append(design_entry)
            results["designs"].append(design_entry)

    # Update stats
    pipeline_data["stats"]["total_designs"] += results["success"]
    pipeline_data["stats"]["designs_today"] = results["success"]
    pipeline_data["stats"]["last_design_at"] = datetime.now(timezone.utc).isoformat()
    pipeline_data["_last_run"] = datetime.now(timezone.utc).isoformat()

    # Save both files
    prompts_path.write_text(
        json.dumps(prompts_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    pipeline_path.write_text(
        json.dumps(pipeline_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\n  Canva batch complete: {results['success']} designed, "
          f"{results['failed']} failed, {results['skipped']} skipped")

    return results


def _build_text_overlay(prompt_item: dict, design_type: str) -> dict:
    """Build text overlay content based on prompt metadata and design type."""
    notes = prompt_item.get("notes", "")
    keywords = prompt_item.get("keywords_targeted", [])

    if design_type == "product_spotlight":
        # Extract model name from keywords or notes
        model = next((k for k in keywords if "iPhone" in k or "Galaxy" in k or "Pixel" in k), "")
        return {
            "headline": model or "Premium Refurbished",
            "subline": "65-Point Inspected. Like New.",
            "cta": "Shop Now",
        }

    elif design_type == "deal_urgency":
        model = next((k for k in keywords if "iPhone" in k or "Galaxy" in k), "")
        return {
            "headline": model or "Flash Deal",
            "subline": "Save 40-60% vs Retail",
            "cta": "Check Price",
        }

    elif design_type == "sustainability":
        return {
            "headline": "Choose Refurbished",
            "subline": "Same phone. Less waste.",
            "cta": "Save Money & Planet",
        }

    elif design_type == "comparison":
        return {
            "headline": "New vs Refurbished",
            "subline": "Same specs. Half the price.",
            "cta": "See the Savings",
        }

    else:  # lifestyle
        return {
            "headline": keywords[0] if keywords else "Premium for Less",
            "subline": "Refurbished. Inspected. Guaranteed.",
            "cta": "Find Yours",
        }


# ---------------------------------------------------------------------------
# Telegram notification
# ---------------------------------------------------------------------------

def notify_canva_batch(results: dict):
    """Send Canva batch results to Telegram."""
    try:
        from actions.telegram_bot import send_message as tg_send

        msg_parts = [
            "<b>CANVAS Designer Report</b>\n",
            f"Designed: {results['success']}",
            f"Failed: {results['failed']}",
            f"Skipped: {results['skipped']}",
        ]

        if results["designs"]:
            msg_parts.append("\n<b>Designs created:</b>")
            for d in results["designs"][:5]:
                status = d["status"]
                platform = d["platform"]
                design_type = d["design_type"]
                msg_parts.append(f"  {platform} / {design_type} — {status}")

        tg_send("\n".join(msg_parts))
    except Exception as e:
        print(f"  (Telegram notify failed: {e})")


# ---------------------------------------------------------------------------
# Main entry point (called from workflow)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  CANVA POST DESIGNER — BATCH RUN")
    print(f"  Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    if not os.environ.get("CANVA_ACCESS_TOKEN"):
        print("ERROR: CANVA_ACCESS_TOKEN not set")
        exit(1)

    results = process_batch()
    notify_canva_batch(results)

    print(f"\n{'=' * 60}")
    print("  CANVA DESIGNER — COMPLETE")
    print(f"{'=' * 60}")
