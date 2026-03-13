#!/usr/bin/env python3
"""
Daily Blog Pipeline Status Report.
Reads blog-pipeline.json and sends a Telegram summary.
Runs daily at 15:00 UTC (8 AM PST / 11 AM EST).
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from actions.telegram_bot import send_message

REPO_ROOT = Path(__file__).parent.parent
PIPELINE_PATH = REPO_ROOT / "departments" / "content" / "blog-pipeline.json"


def build_report() -> str:
    """Build the daily blog status report."""
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    if not PIPELINE_PATH.exists():
        return "⚠️ <b>Blog Pipeline</b>\n\nNo pipeline file found."

    pipeline = json.loads(PIPELINE_PATH.read_text(encoding="utf-8"))
    blogs = pipeline.get("blogs", [])
    stats = pipeline.get("pipeline_stats", {})

    # Categorize blogs
    published_today = []
    drafts = []
    blocked = []
    qa_pending = []

    for blog in blogs:
        status = blog.get("status", "")
        pub_date = blog.get("published_at", "")

        if status == "published" and pub_date and pub_date.startswith(today):
            published_today.append(blog)
        elif status == "published":
            pass  # older published posts, skip
        elif status in ("qa_blocked", "blocked"):
            blocked.append(blog)
        elif status in ("draft_ready", "brief_ready"):
            drafts.append(blog)
        elif status in ("qa_approved", "queued_for_publish"):
            qa_pending.append(blog)

    # Build message
    lines = [f"📰 <b>Daily Blog Report — {now.strftime('%b %d, %Y')}</b>"]
    lines.append(f"🕐 {now.strftime('%H:%M UTC')} ({now.strftime('%I:%M %p')} UTC)\n")

    # Published today
    if published_today:
        lines.append(f"✅ <b>Published Today ({len(published_today)})</b>")
        for b in published_today:
            score = b.get("qa_score", {}).get("rating", "N/A")
            lines.append(f"  • {b['title']}")
            lines.append(f"    QA: {score} | Words: {b.get('word_count', '?')}")
    else:
        lines.append("📝 <b>Published Today</b>: None yet")

    # Ready to publish
    if qa_pending:
        lines.append(f"\n🟢 <b>Ready to Publish ({len(qa_pending)})</b>")
        for b in qa_pending:
            score = b.get("qa_score", {}).get("rating", "N/A")
            lines.append(f"  • {b['title']}")
            lines.append(f"    QA: {score} | Status: {b.get('status', '?')}")

    # Drafts in progress
    if drafts:
        lines.append(f"\n🔵 <b>Drafts in Pipeline ({len(drafts)})</b>")
        for b in drafts:
            lines.append(f"  • {b['title']}")
            lines.append(f"    Status: {b.get('status', '?')}")

    # Blocked
    if blocked:
        lines.append(f"\n🔴 <b>BLOCKED ({len(blocked)})</b>")
        for b in blocked:
            warnings = b.get("qa_warnings", b.get("qa_feedback", []))
            lines.append(f"  • {b['title']}")
            if warnings:
                lines.append(f"    Issues: {len(warnings)} flags")

    # Pipeline stats
    lines.append(f"\n📊 <b>Pipeline Totals</b>")
    lines.append(f"  Drafted: {stats.get('total_drafted', 0)} | "
                 f"Published: {stats.get('total_published', 0)} | "
                 f"Blocked: {stats.get('total_blocked', 0)}")

    # Schedule reminder
    lines.append(f"\n⏰ <b>Next Run</b>")
    lines.append("  SCRIBE: 12:00 UTC (8 AM EST)")
    lines.append("  QUILL:  13:00 UTC (9 AM EST)")
    lines.append("  PRESS:  14:30 UTC (10:30 AM EST)")

    return "\n".join(lines)


def main():
    report = build_report()
    print(report)
    print("\nSending to Telegram...")
    try:
        send_message(report)
        print("Sent.")
    except Exception as e:
        print(f"ERROR sending Telegram: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
