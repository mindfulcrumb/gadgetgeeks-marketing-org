#!/usr/bin/env python3
"""
Core engine for the Gadget Geeks Marketing Organization.
Each GitHub Actions workflow calls this script with a department name.
It loads the department's agent prompt, reads context files, calls Claude API,
parses actions from the response, and commits updated state back to the repo.
"""

import os
import sys
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from actions.github_state import read_state, write_state, commit_changes
from actions.postiz import post_to_social
from actions.resend_email import send_email
from actions.shopify_api import query_shopify
from actions.x_api import run_niche_scan, get_tweet, parse_tweet_url
from actions.telegram_bot import (
    notify_department_start,
    notify_department_complete,
    notify_queue_item,
    notify_error,
    send_message as tg_send,
)

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
DEPARTMENTS_DIR = REPO_ROOT / "departments"
AGENTS_DIR = REPO_ROOT / "agents"
CONFIG_DIR = REPO_ROOT / "config"
STATE_DIR = REPO_ROOT / "state"

# Model selection: opus for GM weekly report, sonnet for everything else
MODELS = {
    "default": "claude-sonnet-4-20250514",
    "gm_report": "claude-opus-4-20250514",
}

# Per-department token limits (blog pipeline needs more for full content)
MAX_TOKENS_DEFAULT = 4096
MAX_TOKENS_OVERRIDE = {
    "blog_writer": 8192,
    "blog_qa": 8192,
    "blog_publish": 16384,
    "gm_report": 8192,
}


# ---------------------------------------------------------------------------
# Department definitions: what each department reads and which agent prompt
# ---------------------------------------------------------------------------
DEPARTMENT_CONFIG = {
    "intel": {
        "agent_prompt": "agents/custom/intel-agent.md",
        "context_files": [
            "departments/intel/competitors.json",
            "departments/intel/trends.json",
            "departments/intel/customer-language.json",
            "config/niche.json",
            "config/competitors-list.json",
        ],
        "output_files": [
            "departments/intel/competitors.json",
            "departments/intel/trends.json",
            "departments/intel/customer-language.json",
        ],
    },
    "seo": {
        "agent_prompt": "agents/custom/seo-agent.md",
        "context_files": [
            "departments/seo/keywords.json",
            "departments/seo/opportunities.json",
            "departments/intel/trends.json",
            "departments/intel/customer-language.json",
            "config/niche.json",
        ],
        "output_files": [
            "departments/seo/keywords.json",
            "departments/seo/opportunities.json",
            "departments/seo/audit-log.md",
            "departments/content/product-copy-queue.json",
        ],
    },
    "seo_weekly": {
        "agent_prompt": "agents/custom/seo-weekly-agent.md",
        "context_files": [
            "departments/seo/keywords.json",
            "departments/seo/opportunities.json",
            "departments/seo/audit-log.md",
            "departments/intel/trends.json",
            "departments/intel/customer-language.json",
            "config/niche.json",
        ],
        "output_files": [
            "departments/seo/keywords.json",
            "departments/seo/opportunities.json",
            "departments/seo/audit-log.md",
        ],
    },
    "content": {
        "agent_prompt": "agents/custom/content-agent.md",
        "context_files": [
            "departments/content/calendar.json",
            "departments/content/product-copy-queue.json",
            "departments/intel/customer-language.json",
            "departments/x-intel/daily-brief.json",
            "config/niche.json",
            "config/copy-rules.json",
        ],
        "output_files": [
            "departments/content/calendar.json",
            "departments/content/product-copy-queue.json",
        ],
    },
    "email": {
        "agent_prompt": "agents/custom/email-marketing-agent.md",
        "context_files": [
            "departments/email/campaigns.json",
            "departments/email/segments.json",
            "departments/email/ab-tests.json",
            "departments/intel/customer-language.json",
            "departments/x-intel/daily-brief.json",
            "config/niche.json",
            "config/copy-rules.json",
        ],
        "output_files": [
            "departments/email/campaigns.json",
            "departments/email/ab-tests.json",
        ],
    },
    "social_morning": {
        "agent_prompt": "agents/custom/social-morning-agent.md",
        "context_files": [
            "departments/social/calendar.json",
            "departments/social/platform-config.json",
            "departments/intel/trends.json",
            "departments/intel/customer-language.json",
            "departments/x-intel/daily-brief.json",
            "config/niche.json",
            "config/copy-rules.json",
        ],
        "output_files": [
            "departments/social/calendar.json",
        ],
    },
    "social_afternoon": {
        "agent_prompt": "agents/custom/social-afternoon-agent.md",
        "context_files": [
            "departments/social/calendar.json",
            "departments/social/engagement-log.md",
            "departments/social/platform-config.json",
        ],
        "output_files": [
            "departments/social/calendar.json",
            "departments/social/engagement-log.md",
        ],
    },
    "cro": {
        "agent_prompt": "agents/custom/cro-agent.md",
        "context_files": [
            "departments/cro/experiments.json",
            "departments/cro/metrics.json",
            "departments/cro/audit-log.md",
            "departments/intel/customer-language.json",
            "config/niche.json",
        ],
        "output_files": [
            "departments/cro/experiments.json",
            "departments/cro/metrics.json",
            "departments/cro/audit-log.md",
        ],
    },
    "x_intel": {
        "agent_prompt": "agents/custom/x-intel-agent.md",
        "context_files": [
            "departments/x-intel/daily-brief.json",
            "departments/intel/trends.json",
            "departments/intel/customer-language.json",
            "config/niche.json",
            "config/competitors-list.json",
        ],
        "output_files": [
            "departments/x-intel/daily-brief.json",
        ],
    },
    "gm_report": {
        "agent_prompt": "agents/custom/gm-report-agent.md",
        "context_files": [
            "state/master.json",
            "state/queue.json",
            "departments/intel/competitors.json",
            "departments/intel/trends.json",
            "departments/intel/customer-language.json",
            "departments/x-intel/daily-brief.json",
            "departments/seo/keywords.json",
            "departments/seo/opportunities.json",
            "departments/seo/audit-log.md",
            "departments/content/calendar.json",
            "departments/email/campaigns.json",
            "departments/email/ab-tests.json",
            "departments/social/calendar.json",
            "departments/social/engagement-log.md",
            "departments/cro/experiments.json",
            "departments/cro/metrics.json",
            "config/niche.json",
        ],
        "output_files": [
            "departments/gm/weekly-report.md",
        ],
    },
    "gm_queue": {
        "agent_prompt": "agents/custom/gm-queue-agent.md",
        "context_files": [
            "state/queue.json",
            "state/master.json",
        ],
        "output_files": [
            "state/queue.json",
            "state/master.json",
        ],
    },
    "image_prompts": {
        "agent_prompt": "agents/custom/image-prompting-agent.md",
        "context_files": [
            "departments/social/calendar.json",
            "departments/social/image-prompts.json",
            "departments/content/calendar.json",
            "departments/x-intel/daily-brief.json",
            "departments/intel/trends.json",
            "departments/seo/keywords.json",
            "config/niche.json",
        ],
        "output_files": [
            "departments/social/image-prompts.json",
        ],
    },
    "prompt_qa": {
        "agent_prompt": "agents/custom/prompt-qa-agent.md",
        "context_files": [
            "departments/social/image-prompts.json",
            "agents/custom/image-prompting-agent.md",
            "agents/custom/department-context.md",
            "config/niche.json",
        ],
        "output_files": [
            "departments/social/image-prompts.json",
        ],
    },
    "blog_writer": {
        "agent_prompt": "agents/custom/blog-writer-agent.md",
        "context_files": [
            "departments/content/blog-pipeline.json",
            "departments/content/calendar.json",
            "departments/intel/trends.json",
            "departments/intel/customer-language.json",
            "departments/x-intel/daily-brief.json",
            "departments/seo/keywords.json",
            "departments/seo/opportunities.json",
            "config/niche.json",
            "config/copy-rules.json",
        ],
        "output_files": [
            "departments/content/blog-pipeline.json",
        ],
    },
    "blog_qa": {
        "agent_prompt": "agents/custom/blog-copy-qa-agent.md",
        "context_files": [
            "departments/content/blog-pipeline.json",
            "config/copy-rules.json",
            "config/niche.json",
            "agents/custom/department-context.md",
        ],
        "output_files": [
            "departments/content/blog-pipeline.json",
        ],
    },
    "blog_publish": {
        "agent_prompt": "agents/custom/blog-publisher-agent.md",
        "context_files": [
            "departments/content/blog-pipeline.json",
            "departments/social/image-prompts.json",
            "config/niche.json",
        ],
        "output_files": [
            "departments/content/blog-pipeline.json",
            "state/queue.json",
        ],
    },
    "dialer": {
        "agent_prompt": "agents/custom/dialer-agent.md",
        "context_files": [
            "departments/dialer/call-list.json",
            "departments/intel/customer-language.json",
            "departments/intel/trends.json",
            "config/niche.json",
            "config/vapi.json",
        ],
        "output_files": [
            "departments/dialer/call-list.json",
            "state/queue.json",
        ],
    },
}


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def _pick_content_topic() -> str:
    """Pick a content topic from SEO opportunities, trends, or X intel."""
    fallbacks = [
        "refurbished iPhone buying guide 2026",
        "best budget phones under $300",
        "refurbished vs new phone comparison",
        "phone battery health check guide",
        "eco-friendly phone accessories roundup",
    ]
    # Try SEO opportunities first
    opps_path = REPO_ROOT / "departments" / "seo" / "opportunities.json"
    if opps_path.exists():
        try:
            opps = json.loads(opps_path.read_text(encoding="utf-8"))
            if isinstance(opps, list) and opps:
                return opps[0].get("topic", opps[0].get("keyword", fallbacks[0]))
            if isinstance(opps, dict) and opps.get("opportunities"):
                return opps["opportunities"][0].get("topic", fallbacks[0])
        except Exception:
            pass
    # Try trends
    trends_path = REPO_ROOT / "departments" / "intel" / "trends.json"
    if trends_path.exists():
        try:
            trends = json.loads(trends_path.read_text(encoding="utf-8"))
            if isinstance(trends, list) and trends:
                return trends[0].get("topic", trends[0].get("trend", fallbacks[0]))
            if isinstance(trends, dict) and trends.get("trends"):
                return trends["trends"][0].get("topic", fallbacks[0])
        except Exception:
            pass
    # Fallback: rotate through defaults based on day of month
    return fallbacks[datetime.now().day % len(fallbacks)]


def load_agent_prompt(dept_config: dict) -> str:
    """Load the agent's system prompt from its .md file."""
    prompt_path = REPO_ROOT / dept_config["agent_prompt"]
    if not prompt_path.exists():
        # Fallback: check original agency-agents directories
        alt_path = REPO_ROOT / "marketing" / prompt_path.name
        if alt_path.exists():
            return alt_path.read_text(encoding="utf-8")
        print(f"WARNING: Agent prompt not found at {prompt_path}")
        return f"You are a marketing department agent. Follow the instructions in your context."
    return prompt_path.read_text(encoding="utf-8")


def load_context(dept_config: dict) -> str:
    """Load all context files and format them for the prompt."""
    context_parts = []
    for file_path in dept_config["context_files"]:
        full_path = REPO_ROOT / file_path
        if full_path.exists():
            content = full_path.read_text(encoding="utf-8")
            context_parts.append(f"=== FILE: {file_path} ===\n{content}\n")
        else:
            context_parts.append(f"=== FILE: {file_path} === [EMPTY - not yet created]\n")
    return "\n".join(context_parts)


def fetch_live_x_data() -> str:
    """Fetch live X/Twitter data for the x_intel department."""
    if not os.environ.get("X_BEARER_TOKEN"):
        return "\n=== LIVE X DATA === [SKIPPED — X_BEARER_TOKEN not set]\n"

    try:
        results = run_niche_scan(max_per_query=10)
        parts = ["\n=== LIVE X DATA (from X API) ===\n"]
        for query_name, data in results.items():
            if "error" in data:
                parts.append(f"\n--- {query_name} --- ERROR: {data['error']}\n")
                continue
            tweets = data.get("data", [])
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
            parts.append(f"\n--- {query_name} ({len(tweets)} tweets) ---")
            for t in tweets:
                author = users.get(t.get("author_id"), {})
                metrics = t.get("public_metrics", {})
                parts.append(
                    f"@{author.get('username', '?')} ({author.get('name', '?')}):"
                    f" {t.get('text', '')[:280]}"
                    f" | likes:{metrics.get('like_count', 0)}"
                    f" rt:{metrics.get('retweet_count', 0)}"
                    f" replies:{metrics.get('reply_count', 0)}"
                    f" | {t.get('created_at', '')}"
                )
        return "\n".join(parts) + "\n"
    except Exception as e:
        return f"\n=== LIVE X DATA === ERROR: {e}\n"


def _get_boss_instructions(department: str) -> str:
    """Check for boss instructions from Telegram for this department."""
    instr_path = STATE_DIR / "boss-instructions.json"
    if not instr_path.exists():
        return ""

    try:
        data = json.loads(instr_path.read_text(encoding="utf-8"))
    except Exception:
        return ""

    pending = data.get("pending", [])
    dept_instructions = []
    remaining = []

    for item in pending:
        if item.get("department") == department and item.get("status") == "pending":
            dept_instructions.append(item)
            item["status"] = "consumed"
            item["consumed_at"] = datetime.now(timezone.utc).isoformat()
        else:
            remaining.append(item)

    if not dept_instructions:
        return ""

    # Save back with consumed status
    data["pending"] = [i for i in data.get("pending", []) if i.get("status") == "pending"]
    data.setdefault("consumed", []).extend(dept_instructions)
    instr_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = ["\n=== BOSS INSTRUCTIONS (from Telegram — HIGHEST PRIORITY) ==="]
    for item in dept_instructions:
        lines.append(f"- [{item.get('created_at', '?')}] {item['instruction']}")
    lines.append("=== END BOSS INSTRUCTIONS ===\n")
    lines.append("IMPORTANT: The boss instructions above take priority over your standard tasks. Execute them FIRST.\n")
    return "\n".join(lines)


def build_user_message(department: str, context: str) -> str:
    """Build the user message with context and instructions."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Check for boss instructions from Telegram
    boss_instructions = _get_boss_instructions(department)

    return f"""Current time: {now}
Department: {department}

Here is your current context (state files from the repository):

{context}
{boss_instructions}
---

Execute your department's tasks now. Read the context above carefully.

IMPORTANT: Return your response in this exact format:

1. First, write your analysis and work in plain text.

2. Then, output any file updates as JSON blocks wrapped in ```json tags with a special header comment:
```json
// UPDATE: path/to/file.json
{{ "the": "updated content" }}
```

3. For any actions that need human approval (emails to send, product descriptions to update on Shopify, theme changes), add them to the queue:
```json
// QUEUE_ITEM
{{
  "type": "email|product_copy|theme_change|social_post",
  "department": "{department}",
  "summary": "Brief description",
  "details": {{ }},
  "created": "{now}"
}}
```

4. For social media posts to publish immediately via Postiz:
```json
// SOCIAL_POST
{{
  "content": "The post text",
  "platforms": ["twitter", "instagram", "facebook"],
  "media_url": null
}}
```
"""


def _try_parse_json(text: str):
    """Try to parse JSON, fixing common issues from LLM output."""
    text = text.strip()
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try wrapping in braces if it starts with a key
    if text.startswith('"') and not text.startswith('{'):
        try:
            return json.loads('{' + text + '}')
        except json.JSONDecodeError:
            pass
    # Try finding the first complete JSON object using brace counting
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    start = None
    return None


def parse_response(response_text: str) -> dict:
    """Parse Claude's response into file updates, queue items, and social posts."""
    result = {
        "analysis": "",
        "file_updates": [],
        "queue_items": [],
        "social_posts": [],
    }

    # Extract JSON blocks with headers
    json_blocks = re.findall(
        r'```json\s*\n\s*//\s*(UPDATE|QUEUE_ITEM|SOCIAL_POST):?\s*(.*?)\n(.*?)```',
        response_text,
        re.DOTALL,
    )

    for block_type, header, content in json_blocks:
        content = content.strip()
        data = _try_parse_json(content)
        if data is None:
            # If it's an UPDATE with non-JSON content (like markdown), treat as raw text
            if block_type == "UPDATE" and header.strip():
                result["file_updates"].append({"path": header.strip(), "data": content})
                continue
            print(f"WARNING: Failed to parse JSON block ({block_type}): {content[:100]}...")
            continue

        if block_type == "UPDATE":
            file_path = header.strip()
            result["file_updates"].append({"path": file_path, "data": data})
        elif block_type == "QUEUE_ITEM":
            result["queue_items"].append(data)
        elif block_type == "SOCIAL_POST":
            result["social_posts"].append(data)

    # Fallback: scan for bare JSON objects with known keys if no blocks found
    if not result["queue_items"] and "blog_publish" in response_text:
        for m in re.finditer(r'\{[^{}]*"type"\s*:\s*"blog_publish"', response_text):
            data = _try_parse_json(response_text[m.start():])
            if data and isinstance(data, dict) and "type" in data:
                result["queue_items"].append(data)
                print(f"  Recovered queue item via fallback parser")

    # Also catch markdown blocks with UPDATE headers
    md_blocks = re.findall(
        r'```(?:markdown|md)\s*\n\s*//\s*UPDATE:?\s*(.*?)\n(.*?)```',
        response_text,
        re.DOTALL,
    )
    for header, content in md_blocks:
        if header.strip():
            result["file_updates"].append({"path": header.strip(), "data": content.strip()})

    # Everything outside JSON blocks is analysis
    analysis = re.sub(r'```json.*?```', '', response_text, flags=re.DOTALL).strip()
    result["analysis"] = analysis

    return result


def execute_actions(department: str, parsed: dict):
    """Execute parsed actions: write files, add to queue, post to social."""

    # 1. Write file updates
    for update in parsed["file_updates"]:
        file_path = REPO_ROOT / update["path"]
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(update["data"], (dict, list)):
            file_path.write_text(
                json.dumps(update["data"], indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        else:
            file_path.write_text(str(update["data"]), encoding="utf-8")
        print(f"  Updated: {update['path']}")

    # 2. Add queue items
    if parsed["queue_items"]:
        queue_path = STATE_DIR / "queue.json"
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
        for item in parsed["queue_items"]:
            item["id"] = f"{department}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            queue["pending"].append(item)
            print(f"  Queued: {item.get('summary', 'unknown')} [{item.get('type', 'unknown')}]")
        queue_path.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")

    # 3. Post to social media (only if Postiz API key is available)
    postiz_key = os.environ.get("POSTIZ_API_KEY")
    for post in parsed["social_posts"]:
        if postiz_key:
            try:
                post_to_social(
                    content=post["content"],
                    platforms=post.get("platforms", []),
                    media_url=post.get("media_url"),
                    api_key=postiz_key,
                )
                print(f"  Posted to social: {post['content'][:60]}...")
            except Exception as e:
                print(f"  ERROR posting to social: {e}")
        else:
            print(f"  SKIPPED social post (no POSTIZ_API_KEY): {post['content'][:60]}...")


def process_approved_emails(parsed: dict):
    """Check if GM queue approved any emails and send them via Resend."""
    resend_key = os.environ.get("RESEND_API_KEY")
    if not resend_key:
        return

    queue_path = STATE_DIR / "queue.json"
    if not queue_path.exists():
        return

    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    sent_count = 0

    for item in queue.get("approved", []):
        if item.get("type") != "email" or item.get("sent"):
            continue
        details = item.get("details", {})
        to = details.get("to") or details.get("segment_emails", [])
        subject = details.get("subject") or details.get("subject_a", "")
        html_body = details.get("html_body") or details.get("body", "")

        if not to or not subject or not html_body:
            print(f"  SKIPPED email {item.get('id')}: missing to/subject/body")
            continue

        try:
            send_email(
                to=to,
                subject=subject,
                html_body=html_body,
                api_key=resend_key,
            )
            item["sent"] = True
            item["sent_at"] = datetime.now(timezone.utc).isoformat()
            sent_count += 1
            print(f"  SENT email: {subject[:60]}...")
            try:
                tg_send(f"\u2709\ufe0f <b>Email sent!</b>\n\nSubject: {subject}\nTo: {to if isinstance(to, str) else f'{len(to)} recipients'}")
            except Exception:
                pass
        except Exception as e:
            print(f"  ERROR sending email {item.get('id')}: {e}")
            try:
                notify_error("email", f"Failed to send: {subject[:40]}... — {e}")
            except Exception:
                pass

    if sent_count:
        queue_path.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Sent {sent_count} approved email(s) via Resend")


def update_master_state(department: str, success: bool):
    """Update master.json with run timestamp and status."""
    master_path = STATE_DIR / "master.json"
    master = json.loads(master_path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat()

    if department not in master["departments"]:
        master["departments"][department] = {"last_run": None, "status": "idle", "runs_total": 0}

    master["departments"][department]["last_run"] = now
    master["departments"][department]["status"] = "ok" if success else "error"
    master["departments"][department]["runs_total"] += 1

    master_path.write_text(json.dumps(master, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Run history — persistent log of every department run
# ---------------------------------------------------------------------------

def _snapshot_output_files(dept_config: dict) -> dict:
    """Snapshot current state of output files for diffing later."""
    snapshots = {}
    for file_path in dept_config.get("output_files", []):
        full_path = REPO_ROOT / file_path
        if full_path.exists():
            snapshots[file_path] = full_path.read_text(encoding="utf-8")
        else:
            snapshots[file_path] = None
    return snapshots


def _diff_snapshots(before: dict, after: dict) -> list:
    """Compare before/after snapshots and return a list of changes."""
    changes = []
    all_files = set(list(before.keys()) + list(after.keys()))
    for f in sorted(all_files):
        b = before.get(f)
        a_path = REPO_ROOT / f
        a = a_path.read_text(encoding="utf-8") if a_path.exists() else None

        if b is None and a is not None:
            changes.append({"file": f, "action": "created", "size": len(a)})
        elif b is not None and a is None:
            changes.append({"file": f, "action": "deleted"})
        elif b != a:
            changes.append({"file": f, "action": "modified", "size": len(a) if a else 0})
    return changes


def log_run_history(department: str, success: bool, model: str,
                    input_tokens: int, output_tokens: int,
                    file_updates: int, queue_items: int,
                    social_posts: int, changes: list,
                    boss_instructions: bool, error_msg: str = ""):
    """Append a run entry to state/run-history.json."""
    history_path = STATE_DIR / "run-history.json"
    try:
        if history_path.exists():
            history = json.loads(history_path.read_text(encoding="utf-8"))
        else:
            history = {"runs": [], "stats": {"total_runs": 0, "total_tokens": 0, "total_errors": 0}}

        now = datetime.now(timezone.utc)
        entry = {
            "id": f"run_{department}_{now.strftime('%Y%m%d_%H%M%S')}",
            "department": department,
            "timestamp": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "status": "ok" if success else "error",
            "model": model,
            "tokens": {"input": input_tokens, "output": output_tokens, "total": input_tokens + output_tokens},
            "actions": {
                "file_updates": file_updates,
                "queue_items": queue_items,
                "social_posts": social_posts,
            },
            "changes": changes,
            "had_boss_instructions": boss_instructions,
        }
        if error_msg:
            entry["error"] = error_msg[:500]

        history["runs"].insert(0, entry)
        # Keep last 500 runs
        history["runs"] = history["runs"][:500]

        # Update aggregate stats
        history["stats"]["total_runs"] += 1
        history["stats"]["total_tokens"] += input_tokens + output_tokens
        if not success:
            history["stats"]["total_errors"] += 1

        # Per-department stats
        dept_stats = history.setdefault("department_stats", {})
        ds = dept_stats.setdefault(department, {"runs": 0, "tokens": 0, "errors": 0, "last_run": ""})
        ds["runs"] += 1
        ds["tokens"] += input_tokens + output_tokens
        ds["last_run"] = now.isoformat()
        if not success:
            ds["errors"] += 1

        history_path.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"  (run-history logging failed: {e})")


def log_department_changelog(department: str, changes: list, summary: str):
    """Append to per-department changelog."""
    changelog_dir = DEPARTMENTS_DIR / department.replace("_", "-") if department.replace("_", "-") in [
        d.name for d in DEPARTMENTS_DIR.iterdir() if d.is_dir()
    ] else DEPARTMENTS_DIR / department
    # Fallback: find the actual directory
    for d in DEPARTMENTS_DIR.iterdir():
        if d.is_dir() and d.name.replace("-", "_") == department:
            changelog_dir = d
            break

    changelog_path = changelog_dir / "changelog.md"
    now = datetime.now(timezone.utc)
    header = f"\n## {now.strftime('%Y-%m-%d %H:%M UTC')}\n"

    lines = [header]
    if changes:
        for c in changes:
            lines.append(f"- **{c['action']}** `{c['file']}`" + (f" ({c.get('size', '?')} bytes)" if 'size' in c else ""))
    else:
        lines.append("- No file changes")
    if summary:
        lines.append(f"\n> {summary[:300]}")
    lines.append("")

    entry = "\n".join(lines)

    if changelog_path.exists():
        existing = changelog_path.read_text(encoding="utf-8")
        # Keep last 100 entries (~50KB max)
        sections = existing.split("\n## ")
        if len(sections) > 100:
            existing = "## ".join(sections[:100])
        changelog_path.write_text(existing + entry, encoding="utf-8")
    else:
        changelog_dir.mkdir(parents=True, exist_ok=True)
        changelog_path.write_text(f"# {department.replace('_', ' ').title()} — Changelog\n{entry}", encoding="utf-8")


def log_alert(department: str, level: str, message: str):
    """Append to persistent alert history."""
    alerts_path = STATE_DIR / "alert-history.json"
    try:
        if alerts_path.exists():
            alerts = json.loads(alerts_path.read_text(encoding="utf-8"))
        else:
            alerts = {"alerts": []}

        alerts["alerts"].insert(0, {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "department": department,
            "level": level,
            "message": message[:500],
        })
        # Keep last 200 alerts
        alerts["alerts"] = alerts["alerts"][:200]
        alerts_path.write_text(json.dumps(alerts, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_department.py <department_name>")
        print(f"Available: {', '.join(DEPARTMENT_CONFIG.keys())}")
        sys.exit(1)

    department = sys.argv[1]

    if department not in DEPARTMENT_CONFIG:
        print(f"ERROR: Unknown department '{department}'")
        print(f"Available: {', '.join(DEPARTMENT_CONFIG.keys())}")
        sys.exit(1)

    dept_config = DEPARTMENT_CONFIG[department]
    model = MODELS.get(department, MODELS["default"])

    print(f"{'='*60}")
    print(f"  MARKETING ORG — {department.upper()} DEPARTMENT")
    print(f"  Model: {model}")
    print(f"  Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")

    # Snapshot output files BEFORE run (for changelog diffing)
    pre_snapshots = _snapshot_output_files(dept_config)

    # Telegram: notify start
    try:
        notify_department_start(department)
    except Exception as e:
        print(f"  (Telegram start notify failed: {e})")

    # 1. Load agent prompt
    print("\n[1/6] Loading agent prompt...")
    system_prompt = load_agent_prompt(dept_config)

    # 2. Load context
    print("[2/6] Loading context files...")
    context = load_context(dept_config)

    # Inject live X data for x_intel department
    if department == "x_intel":
        print("  Fetching live X/Twitter data...")
        context += fetch_live_x_data()

    # 2b. Try CrewAI pipeline for content department
    if department == "content":
        try:
            from crewai_content.crew import run_content_pipeline
            print("  CrewAI pipeline available — using multi-agent content creation")
            use_crewai = True
        except ImportError:
            print("  CrewAI not available — falling back to single-agent mode")
            use_crewai = False

        if use_crewai:
            try:
                topic = _pick_content_topic()
                print(f"  Topic: {topic}")
                result = run_content_pipeline(topic=topic, save_to_disk=True)
                update_master_state(department, True)
                commit_changes(f"[{department}] CrewAI pipeline run — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
                try:
                    notify_department_complete(department, True, file_updates=1, summary=f"CrewAI: {topic}")
                except Exception:
                    pass
                print(f"\n{'='*60}")
                print(f"  {department.upper()} DEPARTMENT — COMPLETE (CrewAI)")
                print(f"{'='*60}")
                return
            except Exception as e:
                print(f"  CrewAI pipeline failed: {e}")
                print("  Falling back to single-agent mode...")

    # 3. Call Claude API
    print("[3/6] Calling Claude API...")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        update_master_state(department, False)
        log_run_history(department, False, model, 0, 0, 0, 0, 0, [], False, "ANTHROPIC_API_KEY not set")
        log_alert(department, "critical", "ANTHROPIC_API_KEY not set")
        try:
            notify_error(department, "ANTHROPIC_API_KEY not set")
        except Exception:
            pass
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS_OVERRIDE.get(department, MAX_TOKENS_DEFAULT),
            system=system_prompt,
            messages=[
                {"role": "user", "content": build_user_message(department, context)},
            ],
        )
        response_text = message.content[0].text
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        print(f"  Response: {len(response_text)} chars, {output_tokens} tokens (in: {input_tokens})")
    except Exception as e:
        print(f"ERROR calling Claude API: {e}")
        update_master_state(department, False)
        log_run_history(department, False, model, 0, 0, 0, 0, 0, [], False, str(e))
        log_alert(department, "critical", f"Claude API error: {e}")
        try:
            notify_error(department, str(e))
        except Exception:
            pass
        sys.exit(1)

    # 4. Parse and execute actions
    print("[4/6] Parsing response and executing actions...")
    parsed = parse_response(response_text)
    print(f"  File updates: {len(parsed['file_updates'])}")
    print(f"  Queue items: {len(parsed['queue_items'])}")
    print(f"  Social posts: {len(parsed['social_posts'])}")

    execute_actions(department, parsed)

    # 4b. If GM queue run, check for approved emails to send
    if department == "gm_queue":
        process_approved_emails(parsed)

    # 5. Update master state and commit
    print("[5/6] Updating state and committing...")
    update_master_state(department, True)

    # 6. Log run history, changelog, and alerts
    print("[6/6] Logging run history and changelog...")
    changes = _diff_snapshots(pre_snapshots, {})  # compare against current files
    summary = parsed.get("analysis", "")[:300] if parsed.get("analysis") else ""

    # Check if boss instructions were consumed
    had_boss = "BOSS INSTRUCTIONS" in context

    log_run_history(
        department=department,
        success=True,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        file_updates=len(parsed["file_updates"]),
        queue_items=len(parsed["queue_items"]),
        social_posts=len(parsed["social_posts"]),
        changes=changes,
        boss_instructions=had_boss,
    )
    log_department_changelog(department, changes, summary)

    if parsed["queue_items"]:
        log_alert(department, "info", f"Queued {len(parsed['queue_items'])} item(s) for approval")

    commit_changes(f"[{department}] Automated run — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    # Telegram: notify completion
    try:
        notify_department_complete(
            department,
            success=True,
            file_updates=len(parsed["file_updates"]),
            queue_items=len(parsed["queue_items"]),
            social_posts=len(parsed["social_posts"]),
            summary=summary,
        )
        # Notify for each queue item that needs approval
        for item in parsed["queue_items"]:
            notify_queue_item(item)
    except Exception as e:
        print(f"  (Telegram complete notify failed: {e})")

    print(f"\n{'='*60}")
    print(f"  {department.upper()} DEPARTMENT — COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
