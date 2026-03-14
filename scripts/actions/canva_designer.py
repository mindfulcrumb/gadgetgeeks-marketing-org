"""
Canva post designer for GadgetGeeks Marketing Organization.

Creates branded social media posts from AI-generated images:
1. Pillow composites the branded post (text overlays, gradient, logo, CTA badge)
2. Upload finished post to Shopify CDN (permanent cloud URL)
3. Push to Canva as a design (team access / manual tweaks)
4. Export from Canva for backup URL

Canva Connect API does NOT support programmatic editing (text/shapes).
All design composition is done locally with Pillow.
"""

import base64
import io
import json
import os
import requests
import time
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CANVA_API_BASE = "https://api.canva.com/rest/v1"
REPO_ROOT = Path(__file__).parent.parent.parent
PRODUCT_PHOTOS_CONFIG = REPO_ROOT / "config" / "product-photos.json"


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
# Pillow — branded post compositor
# ---------------------------------------------------------------------------

# Brand constants
BRAND_PRIMARY = "#C72F8F"
BRAND_SECONDARY = "#0D0D0D"
BRAND_ACCENT = "#5B21A8"
BRAND_TEXT = "#FFFFFF"
BRAND_LOGO = "GADGET GEEKS PRO"
BRAND_TAGLINE = "Premium Refurbished Tech"


# ---------------------------------------------------------------------------
# Product photo loading (Rule 25 — real product photos, never AI phones)
# ---------------------------------------------------------------------------

def _load_product_photo_registry() -> dict:
    """Load the product photo registry from config."""
    if not PRODUCT_PHOTOS_CONFIG.exists():
        return {}
    return json.loads(PRODUCT_PHOTOS_CONFIG.read_text(encoding="utf-8"))


def _get_product_photo(product_photo_id: str):
    """Load a real product photo by ID from the registry.

    Tries local path first, then CDN URL if available.
    Returns raw image bytes or None if not found.
    """
    registry = _load_product_photo_registry()
    product = registry.get("products", {}).get(product_photo_id)
    if not product:
        print(f"    WARNING: Product photo '{product_photo_id}' not in registry")
        return None

    # Try local path first
    local_path = REPO_ROOT / product.get("local_path", "")
    if local_path.exists():
        return local_path.read_bytes()

    # Try CDN URL
    cdn_url = product.get("cdn_url", "")
    if cdn_url:
        try:
            resp = requests.get(cdn_url, timeout=30)
            resp.raise_for_status()
            return resp.content
        except Exception as e:
            print(f"    WARNING: Failed to download product photo from CDN: {e}")

    print(f"    WARNING: Product photo '{product_photo_id}' has no accessible file")
    return None


def composite_product_on_background(
    product_bytes: bytes,
    width: int,
    height: int,
    background_style: str = "dark gradient",
) -> bytes:
    """Place a real product photo on a branded background.

    Used for product_hero, deal_urgency, and comparison designs
    where the phone image MUST be real (Rule 25).

    Args:
        product_bytes: Raw image bytes of the real product photo.
        width:         Target canvas width.
        height:        Target canvas height.
        background_style: "dark gradient", "marble surface", "brand purple", etc.

    Returns:
        PNG bytes of the product on background.
    """
    canvas = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(canvas)

    # Generate background based on style
    bg_colors = {
        "dark gradient": ((13, 13, 13), (40, 20, 60)),
        "brand purple": ((91, 33, 168), (30, 10, 50)),
        "marble surface": ((240, 235, 230), (220, 215, 210)),
        "midnight": ((10, 10, 20), (25, 25, 40)),
    }
    top_color, bottom_color = bg_colors.get(background_style, bg_colors["dark gradient"])

    for y in range(height):
        ratio = y / height
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # Load and resize product photo to fit (max 60% of canvas)
    product_img = Image.open(io.BytesIO(product_bytes)).convert("RGBA")
    max_w = int(width * 0.6)
    max_h = int(height * 0.6)
    product_img.thumbnail((max_w, max_h), Image.LANCZOS)

    # Center the product on canvas
    paste_x = (width - product_img.width) // 2
    paste_y = (height - product_img.height) // 2

    canvas.paste(product_img, (paste_x, paste_y), product_img)

    return canvas


def composite_product_on_scene(
    scene_bytes: bytes,
    product_bytes: bytes,
    width: int,
    height: int,
    position: str = "center-right",
) -> bytes:
    """Composite a real product photo onto an AI-generated scene.

    Used for lifestyle and sustainability designs where AI generates
    the scene and the real product photo is layered on top (Rule 25).

    Args:
        scene_bytes:   Raw bytes of the AI-generated scene (no phone in it).
        product_bytes: Raw bytes of the real product photo.
        width:         Target width.
        height:        Target height.
        position:      Where to place the product: "center-right", "bottom-center", "hand-area".

    Returns:
        PIL Image (RGBA) of the composite — caller adds text overlays.
    """
    scene = Image.open(io.BytesIO(scene_bytes)).convert("RGBA")
    scene = scene.resize((width, height), Image.LANCZOS)

    product_img = Image.open(io.BytesIO(product_bytes)).convert("RGBA")

    # Size product to ~25% of canvas width for natural look in scene
    product_max_w = int(width * 0.25)
    product_max_h = int(height * 0.4)
    product_img.thumbnail((product_max_w, product_max_h), Image.LANCZOS)

    # Position mapping
    positions = {
        "center-right": (int(width * 0.65), int(height * 0.35)),
        "bottom-center": (int(width * 0.38), int(height * 0.55)),
        "hand-area": (int(width * 0.45), int(height * 0.40)),
        "left": (int(width * 0.10), int(height * 0.30)),
    }
    paste_x, paste_y = positions.get(position, positions["center-right"])

    # Add subtle drop shadow for realism
    shadow = Image.new("RGBA", product_img.size, (0, 0, 0, 40))
    scene.paste(shadow, (paste_x + 4, paste_y + 4), shadow)
    scene.paste(product_img, (paste_x, paste_y), product_img)

    return scene


def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a font, falling back to default if custom fonts unavailable."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def composite_branded_post(
    image_bytes: bytes,
    width: int,
    height: int,
    text_overlay: dict,
    design_type: str,
) -> bytes:
    """Composite a branded social media post using Pillow.

    Args:
        image_bytes: Raw image bytes (PNG/JPG from Gemini or CDN).
        width:       Target width in pixels.
        height:      Target height in pixels.
        text_overlay: {"headline": str, "subline": str, "cta": str}
        design_type:  product_spotlight, deal_urgency, lifestyle, etc.

    Returns:
        PNG bytes of the finished branded post.
    """
    # Load and resize the base image
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    img = img.resize((width, height), Image.LANCZOS)

    # Create overlay layer for gradient + text
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # --- Gradient overlay (bottom 40%) for text readability ---
    if design_type in ("product_spotlight", "deal_urgency", "comparison"):
        gradient_start = int(height * 0.55)
        for y in range(gradient_start, height):
            progress = (y - gradient_start) / (height - gradient_start)
            alpha = int(200 * progress)  # 0 → 200 opacity
            draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
    else:
        # Lighter gradient for lifestyle/sustainability
        gradient_start = int(height * 0.65)
        for y in range(gradient_start, height):
            progress = (y - gradient_start) / (height - gradient_start)
            alpha = int(160 * progress)
            draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))

    # Composite gradient onto image
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # --- Text overlays ---
    headline = text_overlay.get("headline", "")
    subline = text_overlay.get("subline", "")
    cta = text_overlay.get("cta", "")

    margin_x = int(width * 0.06)

    if headline:
        font_size = 64 if width >= 1200 else 52 if width >= 1080 else 40
        font = _get_font(font_size, bold=True)
        y_pos = int(height * 0.68) if design_type != "lifestyle" else int(height * 0.72)

        # Text shadow for readability
        draw.text((margin_x + 2, y_pos + 2), headline, font=font, fill=(0, 0, 0, 180))
        draw.text((margin_x, y_pos), headline, font=font, fill=BRAND_TEXT)

    if subline:
        sub_size = 36 if width >= 1200 else 30 if width >= 1080 else 24
        font = _get_font(sub_size, bold=False)
        y_pos = int(height * 0.78) if design_type != "lifestyle" else int(height * 0.82)

        draw.text((margin_x + 1, y_pos + 1), subline, font=font, fill=(0, 0, 0, 140))
        draw.text((margin_x, y_pos), subline, font=font, fill=BRAND_TEXT)

    if cta:
        cta_size = 28 if width >= 1200 else 24 if width >= 1080 else 20
        cta_font = _get_font(cta_size, bold=True)

        # Measure CTA text
        bbox = draw.textbbox((0, 0), cta, font=cta_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        pad_x, pad_y = 24, 12
        badge_w = text_w + pad_x * 2
        badge_h = text_h + pad_y * 2

        badge_x = width - margin_x - badge_w
        badge_y = int(height * 0.88)

        # CTA badge (rounded rectangle)
        pink = _hex_to_rgb(BRAND_PRIMARY)
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
            radius=10,
            fill=(*pink, 230),
        )
        draw.text(
            (badge_x + pad_x, badge_y + pad_y),
            cta, font=cta_font, fill=BRAND_TEXT,
        )

    # --- Logo text (bottom left, subtle) ---
    logo_size = 16 if width >= 1200 else 14 if width >= 1080 else 12
    logo_font = _get_font(logo_size, bold=True)
    logo_y = int(height * 0.94)
    draw.text((margin_x, logo_y), BRAND_LOGO, font=logo_font, fill=(255, 255, 255, 140))

    # Convert to RGB and export as PNG
    final = img.convert("RGB")
    buf = io.BytesIO()
    final.save(buf, format="PNG", quality=95)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Canva API — upload asset + create design (for team access)
# ---------------------------------------------------------------------------

def upload_asset_to_canva(image_bytes: bytes, name: str) -> dict:
    """Upload image bytes to Canva as an asset (binary upload).

    Returns:
        {"job_id": str} or {"asset_id": str}
    """
    headers = _canva_headers()
    # Canva expects binary body with metadata in header
    name_b64 = base64.b64encode(name[:50].encode()).decode()
    headers["Content-Type"] = "application/octet-stream"
    headers["Asset-Upload-Metadata"] = json.dumps({"name_base64": name_b64})

    resp = requests.post(
        f"{CANVA_API_BASE}/asset-uploads",
        headers=headers,
        data=image_bytes,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    job = data.get("job", {})
    if job.get("id"):
        return {"job_id": job["id"]}

    asset = data.get("asset", {})
    return {"asset_id": asset.get("id", "")}


def poll_asset_upload(job_id: str, max_wait: int = 60) -> str:
    """Poll until asset upload completes. Returns asset_id."""
    for _ in range(max_wait // 3):
        time.sleep(3)
        resp = requests.get(
            f"{CANVA_API_BASE}/asset-uploads/{job_id}",
            headers=_canva_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        job = resp.json().get("job", {})
        if job.get("status") == "success":
            return job.get("asset", {}).get("id", "")
        if job.get("status") == "failed":
            raise RuntimeError(f"Asset upload failed: {job.get('error', {})}")
    raise RuntimeError("Asset upload timed out")


def create_canva_design(title: str, width: int, height: int, asset_id: str = "") -> dict:
    """Create a Canva design, optionally pre-populated with an image.

    Returns:
        {"design_id": str, "edit_url": str, "view_url": str}
    """
    body = {
        "design_type": {
            "type": "custom",
            "width": width,
            "height": height,
        },
        "title": title,
    }
    if asset_id:
        body["asset_id"] = asset_id

    resp = requests.post(
        f"{CANVA_API_BASE}/designs",
        headers=_canva_headers(),
        json=body,
        timeout=30,
    )
    resp.raise_for_status()
    design = resp.json().get("design", {})
    return {
        "design_id": design.get("id", ""),
        "edit_url": design.get("urls", {}).get("edit_url", ""),
        "view_url": design.get("urls", {}).get("view_url", ""),
    }


def export_canva_design(design_id: str) -> str:
    """Export a Canva design as PNG. Returns download URL (valid 24h)."""
    resp = requests.post(
        f"{CANVA_API_BASE}/designs/{design_id}/exports",
        headers=_canva_headers(),
        json={"format": {"type": "png"}},
        timeout=15,
    )
    resp.raise_for_status()
    job = resp.json().get("job", {})
    job_id = job.get("id", "")

    if not job_id:
        urls = resp.json().get("job", {}).get("urls", [])
        return urls[0] if urls else ""

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
            return urls[0] if urls else ""
        if status_data.get("status") == "failed":
            raise RuntimeError(f"Export failed: {status_data.get('error', {})}")

    raise RuntimeError("Export timed out")


# ---------------------------------------------------------------------------
# Full pipeline — build branded post end-to-end
# ---------------------------------------------------------------------------

def build_branded_post(
    image_url: str,
    platform: str,
    design_type: str,
    text_overlay: dict,
    prompt_id: str,
    source: str = "ai_generated",
    product_photo_id: str = "",
    composite_product: str = "",
    background_style: str = "dark gradient",
) -> dict:
    """Build a complete branded social media post.

    Pipeline:
    1. Download the raw AI-generated image
    2. Composite branded post with Pillow (text, gradient, logo, CTA)
    3. Upload finished post to Shopify CDN (permanent URL)
    4. Push to Canva as a design (team can edit in browser)

    Returns:
        {
            "export_url": str (Shopify CDN — permanent),
            "canva_design_id": str,
            "canva_edit_url": str,
            "platform": str,
            "dimensions": str,
            "status": str,
        }
    """
    DIMENSIONS = {
        "instagram": (1080, 1080),
        "instagram_story": (1080, 1920),
        "tiktok": (1080, 1920),
        "twitter": (1600, 900),
        "facebook": (1200, 630),
        "linkedin": (1200, 627),
        "pinterest": (1000, 1500),
    }

    width, height = DIMENSIONS.get(platform, (1080, 1080))
    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    title = f"GGP_{platform}_{design_type}_{now}"

    try:
        # --- Rule 25: Product photo source handling ---
        if source == "product_photo" and product_photo_id:
            # Product hero / deal / comparison: use REAL product photo on branded background
            print(f"    Loading real product photo: {product_photo_id}")
            product_bytes = _get_product_photo(product_photo_id)
            if not product_bytes:
                raise RuntimeError(f"Product photo '{product_photo_id}' not found in registry")

            print(f"    Compositing product on branded background ({width}x{height})...")
            product_canvas = composite_product_on_background(
                product_bytes, width, height, background_style,
            )
            # Convert PIL Image to bytes for branded post overlay
            buf = io.BytesIO()
            product_canvas.convert("RGB").save(buf, format="PNG", quality=95)
            raw_bytes = buf.getvalue()

        elif composite_product and image_url:
            # Lifestyle / sustainability: AI scene + real product photo composited in
            print(f"    Downloading AI scene...")
            img_resp = requests.get(image_url, timeout=60)
            img_resp.raise_for_status()
            scene_bytes = img_resp.content

            print(f"    Loading real product photo for composite: {composite_product}")
            product_bytes = _get_product_photo(composite_product)
            if product_bytes:
                print(f"    Compositing product onto scene ({width}x{height})...")
                composite_canvas = composite_product_on_scene(
                    scene_bytes, product_bytes, width, height,
                )
                buf = io.BytesIO()
                composite_canvas.convert("RGB").save(buf, format="PNG", quality=95)
                raw_bytes = buf.getvalue()
            else:
                print(f"    WARNING: Product photo not found, using AI scene as-is")
                raw_bytes = scene_bytes

        else:
            # Standard path: AI-generated image (blog headers, no-phone scenes)
            print(f"    Downloading raw image...")
            img_resp = requests.get(image_url, timeout=60)
            img_resp.raise_for_status()
            raw_bytes = img_resp.content

        # 2. Composite branded post with Pillow (text overlays, gradient, logo, CTA)
        print(f"    Compositing branded post ({width}x{height})...")
        branded_bytes = composite_branded_post(
            raw_bytes, width, height, text_overlay, design_type,
        )
        print(f"    Branded post: {len(branded_bytes):,} bytes")

        # 3. Upload to Shopify CDN (permanent URL)
        cdn_url = ""
        try:
            from image_gen import upload_to_shopify
            cdn_filename = f"canva-{platform}-{prompt_id}-{now}.png"
            print(f"    Uploading to Shopify CDN...")
            cdn_url = upload_to_shopify(branded_bytes, cdn_filename, content_type="image/png")
            print(f"    CDN URL: {cdn_url}")
        except Exception as e:
            print(f"    Warning: Shopify CDN upload failed ({e})")

        # 4. Push to Canva (team access)
        canva_design_id = ""
        canva_edit_url = ""
        try:
            print(f"    Uploading to Canva...")
            upload_result = upload_asset_to_canva(branded_bytes, title)

            asset_id = upload_result.get("asset_id", "")
            if not asset_id and upload_result.get("job_id"):
                asset_id = poll_asset_upload(upload_result["job_id"])

            if asset_id:
                print(f"    Creating Canva design...")
                design = create_canva_design(title, width, height, asset_id=asset_id)
                canva_design_id = design["design_id"]
                canva_edit_url = design["edit_url"]
                print(f"    Canva design: {canva_edit_url}")
        except Exception as e:
            print(f"    Warning: Canva upload failed ({e}), CDN URL still valid")

        return {
            "export_url": cdn_url,
            "canva_design_id": canva_design_id,
            "canva_edit_url": canva_edit_url,
            "platform": platform,
            "dimensions": f"{width}x{height}",
            "status": "exported",
        }

    except Exception as e:
        print(f"  ERROR building branded post for {prompt_id}: {e}")
        return {
            "export_url": "",
            "canva_design_id": "",
            "canva_edit_url": "",
            "platform": platform,
            "dimensions": f"{width}x{height}",
            "status": "error",
            "error": str(e)[:300],
        }


# ---------------------------------------------------------------------------
# Batch processor — processes all pending images
# ---------------------------------------------------------------------------

def process_batch() -> dict:
    """Process all generated images that haven't been designed yet.

    Reads image-prompts.json, creates branded designs for each image
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

    # Build lookup from top-level prompts array (where full dicts live)
    top_prompts = {p["id"]: p for p in prompts_data.get("prompts", []) if isinstance(p, dict) and "id" in p}

    # Process each folder's prompts
    folders = prompts_data.get("folders", {})
    for folder_name, folder_data in folders.items():
        for entry in folder_data.get("prompts", []):
            # Resolve: entry can be a dict (old format) or a string ID (new format)
            if isinstance(entry, str):
                prompt_item = top_prompts.get(entry)
                if not prompt_item:
                    print(f"  SKIP: {entry} — ID not found in top-level prompts")
                    results["skipped"] += 1
                    continue
            elif isinstance(entry, dict):
                prompt_item = entry
            else:
                results["skipped"] += 1
                continue

            # Skip if no image source available
            # Rule 25: product_photo source doesn't need generated_url
            has_product_photo = prompt_item.get("source") == "product_photo" and prompt_item.get("product_photo_id")
            has_generated_url = bool(prompt_item.get("generated_url"))
            if not has_product_photo and not has_generated_url:
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

            # Determine source type (Rule 25)
            item_source = prompt_item.get("source", "ai_generated")
            item_product_photo_id = prompt_item.get("product_photo_id", "")
            item_composite_product = prompt_item.get("composite_product", "")
            item_bg_style = prompt_item.get("background_style", "dark gradient")

            # For product_photo source, we may not have a generated_url
            image_url_for_build = prompt_item.get("generated_url", "")

            # Build the branded post
            result = build_branded_post(
                image_url=image_url_for_build,
                platform=platform,
                design_type=design_type,
                text_overlay=text_overlay,
                prompt_id=prompt_item.get("id", "unknown"),
                source=item_source,
                product_photo_id=item_product_photo_id,
                composite_product=item_composite_product,
                background_style=item_bg_style,
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

    print(f"\n  Batch complete: {results['success']} designed, "
          f"{results['failed']} failed, {results['skipped']} skipped")

    return results


def _build_text_overlay(prompt_item: dict, design_type: str) -> dict:
    """Build text overlay content based on prompt metadata and design type."""
    keywords = prompt_item.get("keywords_targeted", [])

    if design_type == "product_spotlight":
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
    """Send batch results to Telegram."""
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

    has_worker = os.environ.get("CANVA_TOKEN_WORKER_URL") and os.environ.get("WORKER_API_SECRET")
    has_static = os.environ.get("CANVA_ACCESS_TOKEN")
    if not has_worker and not has_static:
        print("WARNING: No Canva token source — designs will skip Canva upload")

    results = process_batch()
    notify_canva_batch(results)

    print(f"\n{'=' * 60}")
    print("  CANVA DESIGNER — COMPLETE")
    print(f"{'=' * 60}")
