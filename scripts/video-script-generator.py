"""
GadgetGeeks Pro — Video Script Generator (Creatify-Ready)
Generates batch UGC-style video scripts formatted for Creatify AI Avatar API.

Output format matches Creatify lipsyncs_v2 API:
  - Scene-by-scene video_inputs array
  - Clean avatar dialogue (no stage directions in spoken text)
  - B-roll cues separated as background instructions
  - Caption settings per scene
  - 9:16 vertical for TikTok / Reels / Shorts

Platforms: TikTok, Instagram Reels, YouTube Shorts
Style: UGC talking head + B-roll with AI avatar
Lengths: 15s, 30s, 60s

Usage:
  python3 video-script-generator.py --product "iPhone 15 Pro" --price 508 --count 20
  python3 video-script-generator.py --all-products --count 10 --length 30
  python3 video-script-generator.py --all-products --count 5 --html ~/Desktop/scripts.html
"""

import json
import random
import argparse
import os
from datetime import datetime


# ---------------------------------------------------------------------------
# Hook banks — avatar speaks these in first 1-3 seconds
# Clean dialogue only — no stage directions
# ---------------------------------------------------------------------------

HOOKS = {
    "shock_price": [
        "I got a {product} for {price} dollars. Not a scam.",
        "{price} bucks for a {product}. Let me show you.",
        "Stop paying {new_price} dollars when you can pay {price}.",
        "Everyone's paying {new_price} for this phone. I paid {price}.",
        "My {product} cost {price} dollars. Here's the catch. There is none.",
    ],
    "question": [
        "Why are you still paying full price for phones?",
        "You know a {product} costs {new_price} dollars new right? What if I told you something.",
        "Would you pay {price} dollars for a phone that looks brand new?",
        "What's the difference between this and a new {product}? About {savings} dollars.",
        "You're telling me people still buy phones at full price?",
    ],
    "story": [
        "I was about to spend {new_price} dollars on a new phone. Then I found this.",
        "My friend laughed when I said I buy refurbished. Then she saw my phone.",
        "I've been buying refurbished for 3 years. Here's what I learned.",
        "I switched from new to refurbished and saved {savings} dollars. Here me out.",
        "They told me refurbished phones are sketchy. Look at this.",
    ],
    "controversy": [
        "New phones are a scam. I said what I said.",
        "Phone companies don't want you to know this.",
        "Stop wasting money on new phones. Seriously.",
        "The phone industry is lying to you about refurbished.",
        "Unpopular opinion. Buying new phones in 2026 is dumb.",
    ],
    "social_proof": [
        "This is the phone over 500 people bought from us this month.",
        "Our customers save an average of {savings} dollars per phone. Here's how.",
        "4 point 8 stars. Over 500 reviews. {price} dollars. {product}.",
        "Everyone in my family uses refurbished now. Here's why.",
        "This is the number one selling refurbished phone in Arizona right now.",
    ],
    "fear": [
        "If you buy a used phone without checking this, you'll get burned.",
        "3 things that can go wrong with used phones. We test for all of them.",
        "Battery health below 80 percent? Throw it away. Ours start at 85 percent plus.",
        "Activation lock. Carrier lock. Water damage. We check all 65 points.",
        "The biggest mistake people make buying used phones online.",
    ],
    "flex": [
        "Same phone. Half the price. Nobody can tell the difference.",
        "{product}. {price} dollars. 85 percent plus battery. You're welcome.",
        "Looking at my phone you'd think I paid {new_price}. I paid {price}.",
        "This {price} dollar phone outperforms your {new_price} dollar phone.",
        "I don't pay full price for anything. Especially not phones.",
    ],
    "arizona_local": [
        "If you're in Tucson and still buying new phones, we need to talk.",
        "Arizona, stop overpaying for phones. Seriously.",
        "Best phone deal in Tucson right now. {price} dollars for a {product}.",
        "We're based right here in Arizona. {product}, {price} dollars, shipped today.",
        "Tucson students. Stop paying full price. {product} for {price} dollars.",
    ],
}

# ---------------------------------------------------------------------------
# Scene banks — each scene = one video_inputs entry in Creatify
# avatar_text = what the avatar says (clean, speakable)
# b_roll = background/visual instruction for that scene
# duration_hint = rough seconds for pacing
# ---------------------------------------------------------------------------

SCENES = {
    "15": [
        # --- Format: show_phone ---
        {
            "scenes": [
                {"avatar_text": "{hook}", "b_roll": "Avatar talking to camera, casual setting, natural lighting", "duration_hint": 4},
                {"avatar_text": "This is certified refurbished. 85 percent plus battery health. Looks brand new.", "b_roll": "Close-up of {product} front and back, slow rotation", "duration_hint": 6},
                {"avatar_text": "{cta}", "b_roll": "Avatar holding phone up, product page URL overlay", "duration_hint": 5},
            ],
            "body_type": "show_phone",
        },
        # --- Format: comparison ---
        {
            "scenes": [
                {"avatar_text": "{hook}", "b_roll": "Avatar talking to camera, energetic", "duration_hint": 4},
                {"avatar_text": "{new_price} dollars new. {price} dollars refurbished. Same phone. Can you even tell?", "b_roll": "Side by side shot of new vs refurbished {product}", "duration_hint": 6},
                {"avatar_text": "{cta}", "b_roll": "Product page with price visible", "duration_hint": 5},
            ],
            "body_type": "comparison",
        },
        # --- Format: testimonial ---
        {
            "scenes": [
                {"avatar_text": "{hook}", "b_roll": "Avatar in casual home/office setting", "duration_hint": 4},
                {"avatar_text": "Got this last week. Battery lasts all day. Not a scratch on it.", "b_roll": "B-roll of {product} screen on, no scratches visible", "duration_hint": 6},
                {"avatar_text": "{cta}", "b_roll": "Avatar smiling, product link overlay", "duration_hint": 5},
            ],
            "body_type": "testimonial",
        },
        # --- Format: quick_stats ---
        {
            "scenes": [
                {"avatar_text": "{hook}", "b_roll": "Avatar talking, animated text overlays appearing", "duration_hint": 4},
                {"avatar_text": "65 point inspection. 85 percent plus battery. 30 day returns. {price} dollars.", "b_roll": "Text overlay animations: checkmark icons with each stat", "duration_hint": 6},
                {"avatar_text": "{cta}", "b_roll": "Product page screenshot with price", "duration_hint": 5},
            ],
            "body_type": "quick_stats",
        },
    ],
    "30": [
        # --- Format: walkthrough ---
        {
            "scenes": [
                {"avatar_text": "{hook}", "b_roll": "Avatar talking to camera, casual UGC style", "duration_hint": 4},
                {"avatar_text": "{product} for {price} dollars. Not a scratch on it.", "b_roll": "Close-up phone front, tilt to show screen clarity", "duration_hint": 5},
                {"avatar_text": "Battery health sitting at {battery_pct} percent. Same cameras as buying new.", "b_roll": "Screen recording showing battery health in settings, then camera app", "duration_hint": 7},
                {"avatar_text": "Every phone gets a 65 point inspection before it ships to you.", "b_roll": "B-roll of phone inspection process, diagnostic tools", "duration_hint": 6},
                {"avatar_text": "{cta}", "b_roll": "Avatar holding phone, website URL overlay", "duration_hint": 5},
            ],
            "body_type": "walkthrough",
        },
        # --- Format: myth_bust ---
        {
            "scenes": [
                {"avatar_text": "{hook}", "b_roll": "Avatar with skeptical/surprised expression", "duration_hint": 4},
                {"avatar_text": "People think refurbished means broken. Look at this. {product}.", "b_roll": "Reveal shot of pristine {product}", "duration_hint": 5},
                {"avatar_text": "{battery_pct} percent battery health. Zero scratches. Comes with cable, charger, everything.", "b_roll": "Quick cuts: battery settings, screen close-up, unboxing contents", "duration_hint": 7},
                {"avatar_text": "The only difference? You saved {savings} dollars.", "b_roll": "Calculator animation showing savings", "duration_hint": 5},
                {"avatar_text": "{cta}", "b_roll": "Avatar smiling confidently, link overlay", "duration_hint": 5},
            ],
            "body_type": "myth_bust",
        },
        # --- Format: problem_solution ---
        {
            "scenes": [
                {"avatar_text": "{hook}", "b_roll": "Avatar looking frustrated/relatable", "duration_hint": 4},
                {"avatar_text": "New phones cost {new_price} dollars. That's insane. So I found a better way.", "b_roll": "Price tag shock visual, then transition swoosh", "duration_hint": 6},
                {"avatar_text": "{product}, refurbished, {price} dollars. 65 point inspection, battery tested, 30 day guarantee.", "b_roll": "Product beauty shot with feature callouts appearing", "duration_hint": 8},
                {"avatar_text": "Same phone. Smart price. {cta}", "b_roll": "Avatar holding phone proudly, website overlay", "duration_hint": 5},
            ],
            "body_type": "problem_solution",
        },
        # --- Format: day_in_life ---
        {
            "scenes": [
                {"avatar_text": "{hook}", "b_roll": "Avatar in morning routine setting", "duration_hint": 4},
                {"avatar_text": "My daily driver. {product}. Paid {price} dollars for it.", "b_roll": "Phone on desk/nightstand, lifestyle shot", "duration_hint": 5},
                {"avatar_text": "Camera still takes incredible photos. Battery at {battery_pct} percent health, still at 40 percent by end of day.", "b_roll": "Sample photos from camera, battery percentage screenshot at evening", "duration_hint": 8},
                {"avatar_text": "Why would I pay {new_price} dollars for the same exact thing? {cta}", "b_roll": "Avatar shrugging, link overlay", "duration_hint": 6},
            ],
            "body_type": "day_in_life",
        },
    ],
    "60": [
        # --- Format: full_review ---
        {
            "scenes": [
                {"avatar_text": "{hook}", "b_roll": "Avatar sitting down, casual setup, natural light", "duration_hint": 4},
                {"avatar_text": "This is a {product}. Refurbished. I paid {price} dollars.", "b_roll": "Hold up phone to camera, slow reveal", "duration_hint": 5},
                {"avatar_text": "Screen is flawless. No scratches, no dead pixels. Not a single dent on the back.", "b_roll": "Extreme close-up screen, then flip to back panel", "duration_hint": 7},
                {"avatar_text": "Battery health sitting at {battery_pct} percent. Same camera as the {new_price} dollar version.", "b_roll": "Settings screenshot, then camera comparison shots", "duration_hint": 7},
                {"avatar_text": "Came with cable, charger, 30 day return policy. They test 65 things before shipping.", "b_roll": "Unboxing contents laid out, inspection checklist visual", "duration_hint": 7},
                {"avatar_text": "I've bought 3 phones from them now. My whole family switched.", "b_roll": "Multiple phones on table, family/friends context", "duration_hint": 5},
                {"avatar_text": "Save yourself {savings} dollars and stop paying new prices for last year's hype. {cta}", "b_roll": "Avatar direct to camera, confident, website URL overlay", "duration_hint": 8},
            ],
            "body_type": "full_review",
        },
        # --- Format: comparison_deep ---
        {
            "scenes": [
                {"avatar_text": "{hook}", "b_roll": "Avatar holding two phones, one in each hand", "duration_hint": 4},
                {"avatar_text": "Let's settle this. Brand new {product}, {new_price} dollars. Refurbished {product}, {price} dollars.", "b_roll": "Split screen with price tags on each phone", "duration_hint": 6},
                {"avatar_text": "Same speed. Same photos. Same build quality.", "b_roll": "Quick cuts: speed test side by side, photo comparison, build close-ups", "duration_hint": 6},
                {"avatar_text": "New phone 100 percent battery health. Refurbished {battery_pct} percent. Both last all day.", "b_roll": "Battery settings side by side, time-lapse of both lasting full day", "duration_hint": 7},
                {"avatar_text": "That's {savings} dollars saved. The only difference is the box it came in. And you threw that away anyway.", "b_roll": "Calculator showing savings, then crushed box visual", "duration_hint": 7},
                {"avatar_text": "{cta}", "b_roll": "Avatar direct to camera, product page overlay", "duration_hint": 5},
            ],
            "body_type": "comparison_deep",
        },
        # --- Format: story_arc ---
        {
            "scenes": [
                {"avatar_text": "{hook}", "b_roll": "Avatar sitting casually, storytelling mode", "duration_hint": 4},
                {"avatar_text": "Six months ago I cracked my phone. Went to buy a new {product}. {new_price} dollars. I almost did it.", "b_roll": "Cracked phone visual, price tag shock", "duration_hint": 7},
                {"avatar_text": "Then my coworker showed me his phone. Same model. Looked brand new. He paid {price} dollars.", "b_roll": "Coworker showing phone, pristine condition reveal", "duration_hint": 7},
                {"avatar_text": "I thought no way. There's gotta be a catch. So I tried it.", "b_roll": "Avatar skeptical face, then transition to unboxing", "duration_hint": 5},
                {"avatar_text": "Arrived in 2 days. 65 point inspection card in the box. Six months later, battery still at {battery_pct} percent. Camera's perfect. Not a single issue.", "b_roll": "Unboxing montage, then 6 months later title card, phone in great condition", "duration_hint": 10},
                {"avatar_text": "I saved {savings} dollars and honestly I feel stupid for ever buying new. {cta}", "b_roll": "Avatar laughing at self, direct to camera, link overlay", "duration_hint": 7},
            ],
            "body_type": "story_arc",
        },
        # --- Format: objection_handler ---
        {
            "scenes": [
                {"avatar_text": "{hook}", "b_roll": "Avatar direct to camera, confident energy", "duration_hint": 4},
                {"avatar_text": "I know what you're thinking. Refurbished? That sounds sketchy. Let me handle every objection.", "b_roll": "Avatar counting on fingers, list appearing", "duration_hint": 5},
                {"avatar_text": "Battery. Every phone has 85 percent plus health, tested with professional diagnostic equipment. Not just what iOS says.", "b_roll": "Diagnostic tool on phone, battery health reading", "duration_hint": 7},
                {"avatar_text": "Scratches. Our Excellent grade looks brand new. Period. Returns. 30 days, no questions, we pay shipping.", "b_roll": "Pristine phone close-up, then return policy visual", "duration_hint": 7},
                {"avatar_text": "Warranty. Covered if anything goes wrong. Locked. Every phone is carrier unlocked, verified before shipping.", "b_roll": "Warranty badge, then carrier unlock verification screen", "duration_hint": 7},
                {"avatar_text": "{product}. {price} dollars. {savings} dollars less than new. What other objection you got? Drop it in the comments. {cta}", "b_roll": "Avatar challenging camera, product overlay, comments animation", "duration_hint": 8},
            ],
            "body_type": "objection_handler",
        },
    ],
}

# ---------------------------------------------------------------------------
# CTA bank — avatar speaks these as the close
# ---------------------------------------------------------------------------

CTAS = {
    "direct": [
        "Link in bio. {product} starting at {price} dollars.",
        "Gadget Geeks Pro dot com. {price} dollars. Go.",
        "Link in bio before they sell out.",
        "Tap the link. Save {savings} dollars. That simple.",
    ],
    "urgency": [
        "These sell out fast. Link in bio.",
        "Spring deal. Won't last. Link in bio.",
        "Only {stock} left at this price. Link in bio.",
        "March is the best month to buy. Link in bio.",
    ],
    "engagement": [
        "Comment PHONE and I'll send you the link.",
        "Save this for later. You'll thank me.",
        "Follow for more phone deals nobody talks about.",
        "Drop your phone model in the comments. I'll find you a deal.",
        "Share this with someone who's about to waste {new_price} dollars on a new phone.",
    ],
    "soft": [
        "Just saying. Do what you want with that information.",
        "Not telling you what to do. Just showing you the math.",
        "Your money. Your call. But {savings} dollars is {savings} dollars.",
    ],
}

# ---------------------------------------------------------------------------
# Voice tone bank — for Creatify voice selection
# ---------------------------------------------------------------------------

VOICE_TONES = {
    "shock_price": "energetic",
    "question": "conversational",
    "story": "natural",
    "controversy": "bold",
    "social_proof": "confident",
    "fear": "serious",
    "flex": "cool",
    "arizona_local": "friendly",
}

# ---------------------------------------------------------------------------
# Product defaults
# ---------------------------------------------------------------------------

DEFAULT_PRODUCTS = [
    {"name": "iPhone 15 Pro", "price": 508, "new_price": 1099, "battery_pct": "91", "stock": 12},
    {"name": "iPhone 13 Pro", "price": 347, "new_price": 799, "battery_pct": "88", "stock": 18},
    {"name": "iPhone 14 Pro", "price": 429, "new_price": 999, "battery_pct": "90", "stock": 8},
    {"name": "iPhone 12", "price": 248, "new_price": 599, "battery_pct": "86", "stock": 24},
    {"name": "Samsung Galaxy S24 Ultra", "price": 529, "new_price": 1299, "battery_pct": "92", "stock": 6},
    {"name": "Samsung Galaxy S23", "price": 319, "new_price": 799, "battery_pct": "89", "stock": 15},
]


# ---------------------------------------------------------------------------
# Template variable replacement
# ---------------------------------------------------------------------------

def _fill(text: str, product: dict, extras: dict = None) -> str:
    """Replace all template variables in text."""
    savings = product["new_price"] - product["price"]
    replacements = {
        "{product}": product["name"],
        "{price}": str(product["price"]),
        "{new_price}": str(product["new_price"]),
        "{savings}": str(savings),
        "{battery_pct}": str(product.get("battery_pct", "88")),
        "{stock}": str(product.get("stock", 10)),
    }
    if extras:
        replacements.update(extras)
    for key, val in replacements.items():
        text = text.replace(key, val)
    return text


# ---------------------------------------------------------------------------
# Generator — outputs Creatify-ready format
# ---------------------------------------------------------------------------

def generate_script(product: dict, length: str = "30", script_id: int = 1) -> dict:
    """Generate a single Creatify-ready video script."""

    # Pick random hook, scene template, and CTA
    hook_cat = random.choice(list(HOOKS.keys()))
    hook_text = random.choice(HOOKS[hook_cat])
    scene_template = random.choice(SCENES[length])
    cta_cat = random.choice(list(CTAS.keys()))
    cta_text = random.choice(CTAS[cta_cat])

    # Fill hook and CTA
    hook_filled = _fill(hook_text, product)
    cta_filled = _fill(cta_text, product)

    # Build Creatify video_inputs — one entry per scene
    video_inputs = []
    full_avatar_script = ""

    for scene in scene_template["scenes"]:
        # Replace {hook} and {cta} placeholders in scene avatar_text
        avatar_text = scene["avatar_text"]
        avatar_text = avatar_text.replace("{hook}", hook_filled)
        avatar_text = avatar_text.replace("{cta}", cta_filled)
        avatar_text = _fill(avatar_text, product)

        b_roll = _fill(scene["b_roll"], product)

        video_inputs.append({
            "character": {
                "type": "avatar",
                "avatar_id": "{{AVATAR_ID}}",
                "avatar_style": "normal",
                "scale": 1.0,
                "offset": {"x": 0.0, "y": 0.0},
                "hidden": False,
            },
            "voice": {
                "type": "text",
                "input_text": avatar_text,
                "voice_id": "{{VOICE_ID}}",
                "volume": 0.8,
            },
            "background": {
                "type": "image",
                "url": "{{B_ROLL_URL}}",
                "fit": "crop",
                "b_roll_description": b_roll,
            },
            "caption_setting": {
                "style": "normal-black",
                "offset": {"x": 0.0, "y": 0.45},
                "font_family": "Montserrat",
                "font_size": 70,
                "hidden": False,
            },
            "duration_hint_seconds": scene["duration_hint"],
        })

        full_avatar_script += avatar_text + " "

    full_avatar_script = full_avatar_script.strip()
    word_count = len(full_avatar_script.split())

    # Creatify-ready payload
    creatify_payload = {
        "video_inputs": video_inputs,
        "aspect_ratio": "9x16",
        "model_version": "aurora_v1_fast",
    }

    return {
        "script_id": f"vid_{datetime.now().strftime('%Y%m%d')}_{script_id:03d}",
        "product": product["name"],
        "price": product["price"],
        "length": f"{length}s",
        "scene_count": len(video_inputs),
        "hook_type": hook_cat,
        "body_type": scene_template["body_type"],
        "cta_type": cta_cat,
        "voice_tone": VOICE_TONES.get(hook_cat, "natural"),
        "hook": hook_filled,
        "cta": cta_filled,
        "full_avatar_script": full_avatar_script,
        "word_count": word_count,
        "scenes": [
            {
                "scene_num": i + 1,
                "avatar_says": vi["voice"]["input_text"],
                "visual": vi["background"]["b_roll_description"],
                "duration": f"~{vi['duration_hint_seconds']}s",
            }
            for i, vi in enumerate(video_inputs)
        ],
        "creatify_payload": creatify_payload,
        "platforms": ["tiktok", "instagram_reels", "youtube_shorts"],
        "test_variables": {
            "hook_type": hook_cat,
            "body_type": scene_template["body_type"],
            "cta_type": cta_cat,
            "length": f"{length}s",
            "voice_tone": VOICE_TONES.get(hook_cat, "natural"),
        },
        "testing_notes": {
            "strategy": "Run 3-5 avatars per script, $20-50 test budget each, 48hr window for winners",
            "metrics": "Watch view-through rate (VTR) and CTR. Kill below 25% VTR after 48hrs.",
            "scale": "Winners get 3x budget increase. Losers get killed. No middle ground.",
        },
    }


def generate_batch(product: dict, count: int = 20, length: str = None) -> list:
    """Generate a batch of script variations for one product."""
    scripts = []
    lengths = ["15", "30", "60"] if length is None else [length]
    for i in range(count):
        l = random.choice(lengths) if length is None else length
        scripts.append(generate_script(product, length=l, script_id=i + 1))
    return scripts


# ---------------------------------------------------------------------------
# HTML report — visual review of all scripts
# ---------------------------------------------------------------------------

def generate_html_report(all_scripts: list, output_path: str):
    """Generate HTML report for reviewing and picking winners."""

    cards_html = ""
    for s in all_scripts:
        hook_color = {
            "shock_price": "#ff4444", "question": "#4488ff", "story": "#44bb44",
            "controversy": "#ff8800", "social_proof": "#aa44ff", "fear": "#ff4466",
            "flex": "#ffaa00", "arizona_local": "#C72F8F",
        }.get(s["hook_type"], "#888")

        cta_color = {
            "direct": "#44cc44", "urgency": "#ff4444",
            "engagement": "#4488ff", "soft": "#888888",
        }.get(s["cta_type"], "#888")

        scenes_html = ""
        for sc in s["scenes"]:
            scenes_html += f"""
          <div class="scene">
            <div class="scene-num">Scene {sc['scene_num']} <span class="dur">{sc['duration']}</span></div>
            <div class="scene-avatar">"{sc['avatar_says']}"</div>
            <div class="scene-visual">{sc['visual']}</div>
          </div>"""

        cards_html += f"""
    <div class="card">
      <div class="card-header">
        <span class="id">{s['script_id']}</span>
        <span class="product">{s['product']} &mdash; ${s['price']}</span>
        <span class="length">{s['length']}</span>
      </div>
      <div class="tags">
        <span class="tag" style="background:{hook_color}">hook: {s['hook_type']}</span>
        <span class="tag" style="background:#336">body: {s['body_type']}</span>
        <span class="tag" style="background:{cta_color}">cta: {s['cta_type']}</span>
        <span class="tag" style="background:#444">voice: {s['voice_tone']}</span>
      </div>
      <div class="scenes-container">
        {scenes_html}
      </div>
      <div class="full-script">
        <div class="label">FULL AVATAR SCRIPT (paste into Creatify)</div>
        <div class="script-text">{s['full_avatar_script']}</div>
      </div>
      <div class="meta">{s['word_count']} words | {s['scene_count']} scenes | Creatify API ready</div>
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GGP Video Scripts &mdash; Creatify Batch</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0a0a0a; color: #e0e0e0; padding: 40px 20px; }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  h1 {{ font-size: 24px; color: #fff; margin-bottom: 4px; }}
  .subtitle {{ color: #888; margin-bottom: 30px; font-size: 14px; }}
  .stats {{ display: flex; gap: 16px; margin-bottom: 30px; flex-wrap: wrap; }}
  .stat {{ background: #141414; border: 1px solid #2a2a2a; border-radius: 8px; padding: 14px 20px; }}
  .stat .num {{ font-size: 24px; font-weight: 700; color: #fff; }}
  .stat .lbl {{ font-size: 11px; color: #888; text-transform: uppercase; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(500px, 1fr)); gap: 16px; }}
  .card {{ background: #141414; border: 1px solid #2a2a2a; border-radius: 12px; padding: 20px; }}
  .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px; }}
  .id {{ color: #666; font-size: 11px; font-family: monospace; }}
  .product {{ color: #fff; font-weight: 600; font-size: 14px; }}
  .length {{ background: #2a2a2a; color: #ccc; padding: 2px 8px; border-radius: 4px; font-size: 12px; }}
  .tags {{ display: flex; gap: 5px; margin-bottom: 14px; flex-wrap: wrap; }}
  .tag {{ padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; color: #fff; text-transform: uppercase; }}
  .scenes-container {{ margin-bottom: 14px; }}
  .scene {{ background: #1a1a1a; border-left: 3px solid #333; padding: 10px 14px; margin-bottom: 6px; border-radius: 0 6px 6px 0; }}
  .scene-num {{ font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }}
  .scene-num .dur {{ color: #444; }}
  .scene-avatar {{ color: #ff8844; font-size: 14px; font-weight: 500; line-height: 1.4; margin-bottom: 4px; }}
  .scene-visual {{ color: #5588aa; font-size: 12px; font-style: italic; }}
  .full-script {{ background: #0d1a0d; border: 1px solid #224422; border-radius: 8px; padding: 14px; margin-bottom: 10px; }}
  .full-script .label {{ font-size: 10px; color: #44aa44; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }}
  .full-script .script-text {{ color: #ccc; font-size: 13px; line-height: 1.5; cursor: text; user-select: all; }}
  .meta {{ color: #555; font-size: 11px; padding-top: 8px; border-top: 1px solid #1a1a1a; }}
  .how-to {{ background: #141414; border: 1px solid #2a2a2a; border-radius: 12px; padding: 24px; margin-bottom: 24px; }}
  .how-to h2 {{ font-size: 16px; color: #fff; margin-bottom: 12px; }}
  .how-to ol {{ margin-left: 20px; font-size: 13px; color: #aaa; line-height: 1.8; }}
  .how-to .tip {{ background: #1a1a0d; border-left: 3px solid #aaaa44; padding: 10px 14px; margin-top: 12px; border-radius: 0 6px 6px 0; font-size: 12px; color: #cccc88; }}
</style>
</head>
<body>
<div class="container">
  <h1>GGP Video Scripts &mdash; Creatify Batch</h1>
  <p class="subtitle">Generated {datetime.now().strftime('%B %d, %Y %I:%M %p')} | UGC AI Avatar + B-Roll | TikTok / Reels / Shorts</p>

  <div class="stats">
    <div class="stat"><div class="num">{len(all_scripts)}</div><div class="lbl">Total Scripts</div></div>
    <div class="stat"><div class="num">{len(set(s['product'] for s in all_scripts))}</div><div class="lbl">Products</div></div>
    <div class="stat"><div class="num">{len(set(s['hook_type'] for s in all_scripts))}</div><div class="lbl">Hook Types</div></div>
    <div class="stat"><div class="num">{len([s for s in all_scripts if s['length']=='15s'])}/{len([s for s in all_scripts if s['length']=='30s'])}/{len([s for s in all_scripts if s['length']=='60s'])}</div><div class="lbl">15s / 30s / 60s</div></div>
  </div>

  <div class="how-to">
    <h2>How to Use in Creatify</h2>
    <ol>
      <li>Pick a script below &mdash; copy the green "Full Avatar Script" text</li>
      <li>In Creatify, go to <strong>AI Avatar</strong> or <strong>UGC Creator</strong></li>
      <li>Paste the script into the script field</li>
      <li>Select avatar + voice tone (see tags on each card)</li>
      <li>Add B-roll backgrounds per scene (visual descriptions are in blue italic)</li>
      <li>Render in <strong>9:16 vertical</strong> for all platforms</li>
      <li>For API users: the full <code>video_inputs</code> payload is in the JSON output file</li>
    </ol>
    <div class="tip">
      <strong>Testing strategy:</strong> Run 3-5 different avatars per winning script. $20-50 test budget each. Kill anything below 25% view-through rate after 48 hours. Scale winners 3x.
    </div>
  </div>

  <div class="grid">
    {cards_html}
  </div>
</div>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)
    print(f"  HTML report: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="GGP Video Script Generator (Creatify-Ready)")
    parser.add_argument("--product", type=str, help="Product name (e.g. 'iPhone 15 Pro')")
    parser.add_argument("--price", type=int, help="Refurbished price")
    parser.add_argument("--new-price", type=int, help="New retail price")
    parser.add_argument("--count", type=int, default=20, help="Scripts per product (default: 20)")
    parser.add_argument("--length", type=str, choices=["15", "30", "60"], help="Force specific length")
    parser.add_argument("--all-products", action="store_true", help="Generate for all default products")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    parser.add_argument("--html", type=str, default=None, help="Output HTML report path")

    args = parser.parse_args()
    all_scripts = []

    if args.all_products:
        for prod in DEFAULT_PRODUCTS:
            all_scripts.extend(generate_batch(prod, count=args.count, length=args.length))
    elif args.product:
        prod = {
            "name": args.product,
            "price": args.price or 399,
            "new_price": args.new_price or 999,
            "battery_pct": "89",
            "stock": 10,
        }
        all_scripts = generate_batch(prod, count=args.count, length=args.length)
    else:
        for prod in DEFAULT_PRODUCTS[:3]:
            all_scripts.extend(generate_batch(prod, count=args.count, length=args.length))

    # Re-number
    for i, s in enumerate(all_scripts):
        s["script_id"] = f"vid_{datetime.now().strftime('%Y%m%d')}_{i+1:03d}"

    # Output JSON (with Creatify payloads)
    output_path = args.output or f"departments/social/video-scripts-{datetime.now().strftime('%Y%m%d')}.json"
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(all_scripts, f, indent=2)
    print(f"  Generated {len(all_scripts)} Creatify-ready scripts -> {output_path}")

    # Output HTML
    html_path = args.html or output_path.replace(".json", ".html")
    generate_html_report(all_scripts, html_path)

    # Summary
    print(f"\n  Hook distribution:")
    hook_counts = {}
    for s in all_scripts:
        hook_counts[s["hook_type"]] = hook_counts.get(s["hook_type"], 0) + 1
    for h, c in sorted(hook_counts.items(), key=lambda x: -x[1]):
        print(f"    {h}: {c}")

    print(f"\n  Body type distribution:")
    body_counts = {}
    for s in all_scripts:
        body_counts[s["body_type"]] = body_counts.get(s["body_type"], 0) + 1
    for b, c in sorted(body_counts.items(), key=lambda x: -x[1]):
        print(f"    {b}: {c}")


if __name__ == "__main__":
    main()
