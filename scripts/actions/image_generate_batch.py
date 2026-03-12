#!/usr/bin/env python3
"""
Batch image generation — takes prompts from image-prompts.json,
generates real images via Google Gemini Imagen 4, uploads to Shopify CDN,
stores URLs back in the prompts file, and notifies via Telegram.
"""

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def main():
    from image_gen import generate_image, upload_to_shopify

    prompts_path = REPO_ROOT / "departments" / "social" / "image-prompts.json"
    if not prompts_path.exists():
        print("No image-prompts.json found")
        return

    data = json.loads(prompts_path.read_text(encoding="utf-8"))
    generated_count = 0
    failed_count = 0
    results = []

    # Process all folders
    for folder_key, folder in (data.get("folders") or {}).items():
        for prompt_item in folder.get("prompts") or []:
            # Skip already generated
            if prompt_item.get("generated_url"):
                continue

            # Generate any prompt that isn't blocked
            qa = (prompt_item.get("qa_status") or "unreviewed").lower()
            if qa == "blocked":
                continue

            prompt_text = prompt_item.get("prompt", "")
            if not prompt_text:
                continue

            aspect = prompt_item.get("aspect_ratio", "16:9")
            pid = prompt_item.get("id", f"prompt_{folder_key}")

            print(f"  Generating: {pid} ({folder_key}) [{aspect}]")

            try:
                result = generate_image(prompt_text, aspect_ratio=aspect)
                image_bytes = result["image_bytes"]
                mime = result["mime_type"]
                ext = "png" if "png" in mime else "jpg"
                filename = f"gg-{pid}.{ext}"

                print(f"    Image generated ({len(image_bytes)} bytes), uploading to Shopify...")

                cdn_url = upload_to_shopify(image_bytes, filename, content_type=mime)

                prompt_item["generated_url"] = cdn_url
                prompt_item["generated_at"] = __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ).isoformat()
                prompt_item["generation_status"] = "done"

                generated_count += 1
                results.append({"id": pid, "url": cdn_url, "folder": folder_key})
                print(f"    Uploaded: {cdn_url}")

            except Exception as e:
                prompt_item["generation_status"] = "error"
                prompt_item["generation_error"] = str(e)[:300]
                failed_count += 1
                results.append({"id": pid, "error": str(e)[:200], "folder": folder_key})
                print(f"    ERROR: {e}")

    # Save updated prompts
    prompts_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nDone: {generated_count} generated, {failed_count} failed")

    # Notify via Telegram
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts" / "actions"))
        from telegram_bot import send_message, send_photo

        if generated_count > 0:
            msg = (
                f"\U0001F3A8 <b>IMAGE GENERATION COMPLETE</b>\n\n"
                f"\u2705 {generated_count} images generated\n"
                f"{f'\u274C {failed_count} failed' if failed_count else ''}\n\n"
            )
            for r in results[:5]:
                if "url" in r:
                    msg += f"\u2022 <b>{r['id']}</b> ({r['folder']})\n"
                else:
                    msg += f"\u274C <b>{r['id']}</b>: {r.get('error','?')[:100]}\n"
            send_message(msg)

            # Send first generated image as photo preview
            for r in results:
                if "url" in r:
                    try:
                        send_photo(r["url"], caption=f"\U0001F3A8 {r['id']} — {r['folder']}")
                    except Exception:
                        pass
                    break

        elif failed_count > 0:
            send_message(
                f"\u274C <b>IMAGE GENERATION FAILED</b>\n\n"
                f"All {failed_count} prompts failed.\n"
                f"Check GEMINI_API_KEY and Shopify credentials."
            )
        else:
            send_message("\U0001F3A8 No new prompts to generate — all images already exist or prompts are blocked.")

    except Exception as tg_err:
        print(f"Telegram notify error: {tg_err}")


if __name__ == "__main__":
    main()
