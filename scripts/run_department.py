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

MAX_TOKENS = 8192


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
            "departments/social/image-prompts.json",
            "departments/canva/pipeline.json",
            "departments/social/engagement-log.md",
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
            "departments/social/lens-focus-feedback.json",
            "departments/canva/pipeline.json",
        ],
        "output_files": [
            "departments/social/calendar.json",
            "departments/social/engagement-log.md",
            "departments/social/lens-focus-feedback.json",
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
            "departments/social/lens-focus-feedback.json",
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
            "departments/social/lens-focus-feedback.json",
            "agents/custom/image-prompting-agent.md",
            "agents/custom/department-context.md",
            "config/niche.json",
        ],
        "output_files": [
            "departments/social/image-prompts.json",
            "departments/social/lens-focus-feedback.json",
        ],
    },
    "blog_writer": {
        "agent_prompt": "agents/custom/blog-writer-agent.md",
        "context_files": [
            "departments/content/blog-pipeline.json",
            "departments/intel/customer-language.json",
            "departments/intel/trends.json",
            "departments/x-intel/daily-brief.json",
            "departments/seo/keywords.json",
            "config/niche.json",
            "config/copy-rules.json",
        ],
        "output_files": [
            "departments/content/blog-pipeline.json",
        ],
    },
    "blog_qa": {
        "agent_prompt": "agents/custom/blog-qa-agent.md",
        "context_files": [
            "departments/content/blog-pipeline.json",
            "config/copy-rules.json",
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
            "state/queue.json",
        ],
        "output_files": [
            "departments/content/blog-pipeline.json",
            "state/queue.json",
        ],
    },
    "dialer": {
        "agent_prompt": "agents/custom/dialer-agent.md",
        "context_files": [
            "state/queue.json",
            "config/niche.json",
        ],
        "output_files": [
            "state/queue.json",
        ],
    },
    "standup": {
        "agent_prompt": "agents/custom/chief-of-staff-agent.md",
        "context_files": [
            "state/master.json",
            "state/queue.json",
            "state/incident-log.json",
            "state/shift-handoff.json",
            "departments/content/blog-pipeline.json",
            "departments/social/calendar.json",
            "departments/seo/keywords.json",
            "config/niche.json",
        ],
        "output_files": [
            "state/master.json",
            "state/queue.json",
        ],
    },
    "retro": {
        "agent_prompt": "agents/custom/chief-of-staff-agent.md",
        "context_files": [
            "state/master.json",
            "state/queue.json",
            "state/incident-log.json",
            "state/shift-handoff.json",
            "departments/content/blog-pipeline.json",
            "departments/social/calendar.json",
            "departments/social/engagement-log.md",
            "config/niche.json",
        ],
        "output_files": [
            "state/shift-handoff.json",
            "state/queue.json",
        ],
    },
    "board_meeting": {
        "agent_prompt": "agents/custom/chief-of-staff-agent.md",
        "context_files": [
            "state/master.json",
            "state/queue.json",
            "state/run-history.json",
            "departments/gm/weekly-report.md",
            "departments/intel/competitors.json",
            "departments/intel/trends.json",
            "departments/seo/keywords.json",
            "departments/seo/opportunities.json",
            "departments/social/calendar.json",
            "departments/cro/experiments.json",
            "departments/email/campaigns.json",
            "config/niche.json",
        ],
        "output_files": [
            "departments/gm/weekly-board-minutes.md",
            "state/queue.json",
        ],
    },
    "night_ops": {
        "agent_prompt": "agents/custom/night-ops-agent.md",
        "context_files": [
            "state/master.json",
            "state/queue.json",
            "state/incident-log.json",
            "state/alert-history.json",
            "state/shift-handoff.json",
            "state/run-history.json",
            "departments/content/blog-pipeline.json",
            "config/daily-schedule.json",
            "config/niche.json",
        ],
        "output_files": [
            "state/incident-log.json",
            "state/alert-history.json",
            "state/shift-handoff.json",
            "state/queue.json",
        ],
    },
    "google_trends": {
        "agent_prompt": "agents/custom/google-trends-agent.md",
        "context_files": [
            "departments/intel/trends.json",
            "departments/trends/daily-trends.json",
            "departments/trends/trending-briefs.json",
            "departments/seo/keywords.json",
            "departments/seo/opportunities.json",
            "config/niche.json",
        ],
        "output_files": [
            "departments/trends/daily-trends.json",
            "departments/trends/trending-briefs.json",
            "departments/intel/trends.json",
        ],
    },
    "analytics": {
        "agent_prompt": "agents/custom/analytics-agent.md",
        "context_files": [
            "departments/analytics/google-api-data.json",
            "departments/analytics/daily-report.json",
            "departments/analytics/optimization-queue.json",
            "departments/seo/keywords.json",
            "departments/seo/opportunities.json",
            "departments/content/blog-pipeline.json",
            "departments/intel/trends.json",
            "state/incident-log.json",
            "config/niche.json",
        ],
        "output_files": [
            "departments/analytics/daily-report.json",
            "departments/analytics/optimization-queue.json",
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


def build_user_message(department: str, context: str) -> str:
    """Build the user message with context and instructions."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""Current time: {now}
Department: {department}

Here is your current context (state files from the repository):

{context}

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
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Strategy 1: Replace literal newlines inside JSON string values
            try:
                fixed = re.sub(r'(?<=": ")(.*?)(?="[,\s}])', lambda m: m.group(0).replace('\n', '\\n'), content, flags=re.DOTALL)
                data = json.loads(fixed)
            except (json.JSONDecodeError, Exception):
                # Strategy 2: Extract the first { ... } object manually
                try:
                    brace_start = content.index('{')
                    depth = 0
                    brace_end = brace_start
                    for i, ch in enumerate(content[brace_start:], brace_start):
                        if ch == '{':
                            depth += 1
                        elif ch == '}':
                            depth -= 1
                            if depth == 0:
                                brace_end = i + 1
                                break
                    obj_str = content[brace_start:brace_end]
                    # Escape newlines inside strings
                    obj_fixed = re.sub(r'(?<=": ")(.*?)(?="[,\s}])', lambda m: m.group(0).replace('\n', '\\n'), obj_str, flags=re.DOTALL)
                    data = json.loads(obj_fixed)
                except (ValueError, json.JSONDecodeError):
                    # Strategy 3: json_repair as final fallback
                    try:
                        import json_repair
                        data = json_repair.loads(content)
                    except Exception:
                        if block_type == "UPDATE" and header.strip():
                            result["file_updates"].append({"path": header.strip(), "data": content})
                            continue
                        print(f"WARNING: Failed to parse JSON block ({block_type}): {content[:100]}...")
                        continue

        if block_type == "UPDATE":
            file_path = header.strip()
            result["file_updates"].append({"path": file_path, "data": data})
        elif block_type == "QUEUE_ITEM":
            if isinstance(data, dict):
                result["queue_items"].append(data)
            else:
                print(f"WARNING: QUEUE_ITEM parsed as {type(data).__name__}, skipping")
        elif block_type == "SOCIAL_POST":
            if isinstance(data, dict) and "content" in data:
                result["social_posts"].append(data)
            elif isinstance(data, list):
                # json_repair may return a list if JSON was malformed — try to find a dict in it
                for item in data:
                    if isinstance(item, dict) and "content" in item:
                        result["social_posts"].append(item)
                        break
                else:
                    print(f"WARNING: SOCIAL_POST parsed as list with no valid post dict: {str(data)[:100]}")
            else:
                print(f"WARNING: SOCIAL_POST parsed as {type(data).__name__}, skipping: {str(data)[:100]}")

    # Fallback: Direct scan for SOCIAL_POST blocks by finding // SOCIAL_POST + next {...}
    if not result["social_posts"]:
        for match in re.finditer(r'//\s*SOCIAL_POST', response_text):
            start = match.end()
            # Find the next { after the marker
            brace_pos = response_text.find('{', start)
            if brace_pos == -1 or brace_pos - start > 50:
                continue
            # Brace-match to find the closing }
            depth = 0
            end_pos = brace_pos
            for i in range(brace_pos, min(brace_pos + 5000, len(response_text))):
                if response_text[i] == '{':
                    depth += 1
                elif response_text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end_pos = i + 1
                        break
            raw_obj = response_text[brace_pos:end_pos]
            # Try parsing with newline escaping
            try:
                data = json.loads(raw_obj)
            except json.JSONDecodeError:
                try:
                    fixed = re.sub(r'(?<=": ")(.*?)(?="[,\s}])', lambda m: m.group(0).replace('\n', '\\n'), raw_obj, flags=re.DOTALL)
                    data = json.loads(fixed)
                except (json.JSONDecodeError, Exception):
                    try:
                        import json_repair
                        data = json_repair.loads(raw_obj)
                    except Exception:
                        print(f"WARNING: Fallback SOCIAL_POST scan failed: {raw_obj[:100]}...")
                        continue
            if isinstance(data, dict) and "content" in data:
                result["social_posts"].append(data)
                print(f"  Recovered SOCIAL_POST via fallback scan: {str(data.get('content', ''))[:60]}...")

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
    for idx, post in enumerate(parsed["social_posts"]):
        print(f"  Social post #{idx+1}: type={type(post).__name__}, keys={list(post.keys()) if isinstance(post, dict) else 'N/A'}")
        print(f"  Social post #{idx+1} content: {str(post.get('content', ''))[:80] if isinstance(post, dict) else str(post)[:80]}...")
        print(f"  Social post #{idx+1} media_url: {post.get('media_url', 'NONE') if isinstance(post, dict) else 'N/A'}")
        print(f"  Social post #{idx+1} platforms: {post.get('platforms', []) if isinstance(post, dict) else 'N/A'}")
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
                import traceback
                print(f"  ERROR posting to social: {e}")
                traceback.print_exc()
        else:
            print(f"  SKIPPED social post (no POSTIZ_API_KEY): {post['content'][:60]}...")


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

    # 1. Load agent prompt
    print("\n[1/5] Loading agent prompt...")
    system_prompt = load_agent_prompt(dept_config)

    # 2. Load context
    print("[2/5] Loading context files...")
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
                print(f"\n{'='*60}")
                print(f"  {department.upper()} DEPARTMENT — COMPLETE (CrewAI)")
                print(f"{'='*60}")
                return
            except Exception as e:
                print(f"  CrewAI pipeline failed: {e}")
                print("  Falling back to single-agent mode...")

    # 3. Call Claude API
    print("[3/5] Calling Claude API...")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        update_master_state(department, False)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=[
                {"role": "user", "content": build_user_message(department, context)},
            ],
        )
        response_text = message.content[0].text
        print(f"  Response: {len(response_text)} chars, {message.usage.output_tokens} tokens")
    except Exception as e:
        print(f"ERROR calling Claude API: {e}")
        update_master_state(department, False)
        sys.exit(1)

    # 4. Parse and execute actions
    print("[4/5] Parsing response and executing actions...")
    parsed = parse_response(response_text)
    print(f"  File updates: {len(parsed['file_updates'])}")
    print(f"  Queue items: {len(parsed['queue_items'])}")
    print(f"  Social posts: {len(parsed['social_posts'])}")

    execute_actions(department, parsed)

    # 5. Update master state and commit
    print("[5/5] Updating state and committing...")
    update_master_state(department, True)
    commit_changes(f"[{department}] Automated run — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    print(f"\n{'='*60}")
    print(f"  {department.upper()} DEPARTMENT — COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
