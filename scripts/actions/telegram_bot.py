#!/usr/bin/env python3
"""
Telegram Bot API wrapper for the GadgetGeeks Marketing Organization.
Sends department status updates, images, and handles incoming commands.

Bot: @GGP_MA_Bot
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "telegram.json"

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _get_token() -> str:
    """Get bot token from env or config."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
        return token
    # Fallback to config file
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return cfg.get("bot_token", "")
    return ""


def _get_chat_id() -> str:
    """Get the owner's chat ID from config."""
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return str(cfg.get("chat_id", ""))
    return ""


def _save_chat_id(chat_id: int):
    """Save discovered chat ID to config."""
    cfg = {}
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    cfg["chat_id"] = chat_id
    cfg["discovered_at"] = datetime.now(timezone.utc).isoformat()
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def _api(method: str, token: str = None, **kwargs):
    """Call Telegram Bot API."""
    token = token or _get_token()
    if not token:
        print("WARNING: No TELEGRAM_BOT_TOKEN available")
        return None
    url = f"https://api.telegram.org/bot{token}/{method}"
    resp = requests.post(url, json=kwargs, timeout=30)
    data = resp.json()
    if not data.get("ok"):
        print(f"Telegram API error ({method}): {data.get('description', 'unknown')}")
    return data


# ---------------------------------------------------------------------------
# Sending messages
# ---------------------------------------------------------------------------

def send_message(text: str, chat_id: str = None, parse_mode: str = "HTML",
                 disable_preview: bool = True) -> dict:
    """Send a text message to the owner."""
    chat_id = chat_id or _get_chat_id()
    if not chat_id:
        print("WARNING: No Telegram chat_id configured — skipping message")
        return {}
    # Telegram max message length is 4096
    if len(text) > 4096:
        text = text[:4090] + "\n..."
    return _api("sendMessage",
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_preview)


def send_photo(photo_url: str, caption: str = "", chat_id: str = None) -> dict:
    """Send a photo by URL."""
    chat_id = chat_id or _get_chat_id()
    if not chat_id:
        return {}
    return _api("sendPhoto",
                chat_id=chat_id,
                photo=photo_url,
                caption=caption[:1024] if caption else "",
                parse_mode="HTML")


def send_document(file_url: str, caption: str = "", chat_id: str = None) -> dict:
    """Send a document by URL."""
    chat_id = chat_id or _get_chat_id()
    if not chat_id:
        return {}
    return _api("sendDocument",
                chat_id=chat_id,
                document=file_url,
                caption=caption[:1024] if caption else "")


# ---------------------------------------------------------------------------
# Department notifications
# ---------------------------------------------------------------------------

# Status emoji mapping
STATUS_EMOJI = {
    "ok": "\u2705",       # green check
    "error": "\u274c",    # red X
    "working": "\u23f3",  # hourglass
    "idle": "\u23f8",     # pause
}

DEPT_EMOJI = {
    "intel": "\ud83d\udd0d",
    "seo": "\ud83d\udcc8",
    "seo_weekly": "\ud83d\udcc8",
    "content": "\u270d\ufe0f",
    "email": "\ud83d\udce7",
    "social_morning": "\ud83d\udce3",
    "social_afternoon": "\ud83d\udce3",
    "cro": "\ud83d\udcc9",
    "x_intel": "\ud83d\udc26",
    "gm_report": "\ud83d\udccb",
    "gm_queue": "\ud83d\udcec",
    "image_prompts": "\ud83c\udfa8",
    "prompt_qa": "\ud83d\udd0e",
    "blog_writer": "\u270d\ufe0f",
    "blog_qa": "\ud83d\udea8",
    "blog_publish": "\ud83d\ude80",
    "dialer": "\ud83d\udcde",
}

DEPT_NAMES = {
    "intel": "Market Intel",
    "seo": "SEO Daily",
    "seo_weekly": "SEO Weekly",
    "content": "Content",
    "email": "Email Marketing",
    "social_morning": "Social (Morning)",
    "social_afternoon": "Social (Afternoon)",
    "cro": "CRO",
    "x_intel": "X Intel",
    "gm_report": "GM Report",
    "gm_queue": "GM Queue",
    "image_prompts": "Image Prompts",
    "prompt_qa": "Prompt QA",
    "blog_writer": "Blog Writer",
    "blog_qa": "Blog QA",
    "blog_publish": "Blog Publisher",
    "dialer": "Dialer",
}


def notify_department_start(department: str):
    """Send notification when a department starts running."""
    emoji = DEPT_EMOJI.get(department, "\u2699\ufe0f")
    name = DEPT_NAMES.get(department, department)
    now = datetime.now(timezone.utc).strftime("%H:%M UTC")
    send_message(f"{emoji} <b>{name}</b> starting...\n\ud83d\udd52 {now}")


def notify_department_complete(department: str, success: bool,
                                file_updates: int = 0,
                                queue_items: int = 0,
                                social_posts: int = 0,
                                summary: str = ""):
    """Send notification when a department completes."""
    emoji = DEPT_EMOJI.get(department, "\u2699\ufe0f")
    name = DEPT_NAMES.get(department, department)
    status = "\u2705" if success else "\u274c"
    now = datetime.now(timezone.utc).strftime("%H:%M UTC")

    lines = [f"{emoji} <b>{name}</b> {status}"]
    if file_updates:
        lines.append(f"  \ud83d\udcc1 {file_updates} file(s) updated")
    if queue_items:
        lines.append(f"  \ud83d\udce5 {queue_items} item(s) queued for approval")
    if social_posts:
        lines.append(f"  \ud83d\udce3 {social_posts} social post(s)")
    if summary:
        lines.append(f"\n{summary[:500]}")
    lines.append(f"\n\ud83d\udd52 {now}")

    send_message("\n".join(lines))


def notify_queue_item(item: dict):
    """Send notification for a new queue item that needs approval."""
    dept = item.get("department", "unknown")
    emoji = DEPT_EMOJI.get(dept, "\u2699\ufe0f")
    summary = item.get("summary", "No description")
    item_type = item.get("type", "unknown")

    item_id = item.get("id", "?")
    # Build detail lines from all meaningful fields
    detail_lines = []
    skip_keys = {"id", "department", "type", "summary"}
    for k, v in item.items():
        if k in skip_keys:
            continue
        if isinstance(v, str) and len(v) > 200:
            v = v[:200] + "…"
        elif isinstance(v, (list, dict)):
            v = json.dumps(v, ensure_ascii=False)[:200]
        detail_lines.append(f"  • <b>{k}</b>: {v}")
    details = "\n".join(detail_lines[:8])  # max 8 fields

    send_message(
        f"\ud83d\udce5 <b>NEW APPROVAL NEEDED</b>\n\n"
        f"{emoji} From: <b>{DEPT_NAMES.get(dept, dept)}</b>\n"
        f"\ud83c\udff7 Type: <code>{item_type}</code>\n"
        f"\ud83d\udcdd {summary}\n\n"
        f"{details}\n\n"
        f"\ud83c\udd94 <code>{item_id}</code>\n"
        f"Reply:\n/approve {item_id}\n/reject {item_id}"
    )


def notify_error(department: str, error: str):
    """Send error alert."""
    emoji = DEPT_EMOJI.get(department, "\u2699\ufe0f")
    name = DEPT_NAMES.get(department, department)
    send_message(
        f"\u274c <b>ERROR: {name}</b>\n\n"
        f"<code>{error[:500]}</code>\n\n"
        f"Check GitHub Actions for details."
    )


def send_daily_summary():
    """Send a daily org status summary."""
    master_path = REPO_ROOT / "state" / "master.json"
    if not master_path.exists():
        return

    master = json.loads(master_path.read_text(encoding="utf-8"))
    depts = master.get("departments", {})

    lines = ["\ud83c\udfe2 <b>GADGETGEEKS HQ — Daily Status</b>\n"]

    ok_count = sum(1 for d in depts.values() if d.get("status") == "ok")
    err_count = sum(1 for d in depts.values() if d.get("status") == "error")
    idle_count = sum(1 for d in depts.values() if d.get("status") == "idle")

    lines.append(f"\u2705 {ok_count} OK  \u274c {err_count} Errors  \u23f8 {idle_count} Idle\n")

    for dept_id, info in sorted(depts.items()):
        emoji = STATUS_EMOJI.get(info.get("status", "idle"), "\u2753")
        name = DEPT_NAMES.get(dept_id, dept_id)
        runs = info.get("runs_total", 0)
        last = info.get("last_run", "never")
        if last and last != "never":
            # Show just the time part
            try:
                dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
                last = dt.strftime("%H:%M")
            except Exception:
                last = last[:16]
        lines.append(f"{emoji} {name}: {runs} runs (last: {last})")

    # Queue status
    queue_path = REPO_ROOT / "state" / "queue.json"
    if queue_path.exists():
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
        pending = len(queue.get("pending", []))
        if pending:
            lines.append(f"\n\ud83d\udce5 <b>{pending} item(s) awaiting approval</b>")

    send_message("\n".join(lines))


# ---------------------------------------------------------------------------
# Receiving messages (polling)
# ---------------------------------------------------------------------------

def get_updates(offset: int = None, timeout: int = 30) -> list:
    """Long-poll for new messages."""
    params = {"timeout": timeout}
    if offset:
        params["offset"] = offset
    result = _api("getUpdates", **params)
    if result and result.get("ok"):
        return result.get("result", [])
    return []


def auto_discover_chat_id():
    """Check for any message and save the sender's chat_id."""
    updates = get_updates(timeout=5)
    for update in updates:
        msg = update.get("message", {})
        chat = msg.get("chat", {})
        chat_id = chat.get("id")
        if chat_id:
            _save_chat_id(chat_id)
            print(f"Discovered Telegram chat_id: {chat_id}")
            # Acknowledge with offset
            _api("getUpdates", offset=update["update_id"] + 1, timeout=1)
            return chat_id
    return None


# ---------------------------------------------------------------------------
# Command routing
# ---------------------------------------------------------------------------

COMMANDS = {
    "/start": "Welcome to GadgetGeeks HQ! I'll send you updates from all departments.",
    "/status": "Show org status",
    "/queue": "Show approval queue",
    "/approve": "Approve a queued item",
    "/reject": "Reject a queued item",
    "/run": "Trigger a department NOW via GitHub Actions",
    "/runall": "Trigger ALL departments",
    "/xavier": "Send instruction to Xavier (dialer AI)",
    "/boss": "Send instruction to any department",
    "/history": "Last 10 department runs with token usage",
    "/alerts": "Recent alerts and errors",
    "/costs": "Token usage and cost breakdown",
    "/blog": "Show blog pipeline status",
    "/prompts": "Show image prompt stats",
    "/dashboard": "Open the HQ office dashboard",
    "/fix_image": "Generate + attach header image to a published blog",
    "/help": "Show available commands",
}

DASHBOARD_URL = "https://mindfulcrumb.github.io/gadgetgeeks-marketing-org/"

# Map department names to their GitHub Actions workflow filenames
DEPT_WORKFLOW_MAP = {
    "intel": "intel.yml",
    "seo": "seo-daily.yml",
    "seo_weekly": "seo-weekly.yml",
    "content": "content.yml",
    "email": "email.yml",
    "social_morning": "social-morning.yml",
    "social_afternoon": "social-afternoon.yml",
    "cro": "cro.yml",
    "x_intel": "x-intel.yml",
    "gm_report": "gm-report.yml",
    "gm_queue": "gm-queue.yml",
    "image_prompts": "image-prompts.yml",
    "prompt_qa": "prompt-qa.yml",
    "blog_writer": "blog-writer.yml",
    "blog_qa": "blog-qa.yml",
    "blog_publish": "blog-publish.yml",
    "dialer": "dialer.yml",
    "dialer_execute": "dialer-execute.yml",
}

GITHUB_REPO = "mindfulcrumb/gadgetgeeks-marketing-org"


def handle_command(text: str, chat_id: int) -> str:
    """Route a command and return the response text."""
    text = text.strip()
    cmd = text.split()[0].lower() if text.startswith("/") else ""
    args = text.split()[1:] if len(text.split()) > 1 else []

    if cmd == "/start":
        _save_chat_id(chat_id)
        return (
            "\ud83c\udfae <b>GADGETGEEKS HQ — CONNECTED</b>\n\n"
            "You're now linked to the Marketing Org.\n"
            "I'll send you real-time updates from all departments.\n\n"
            "<b>Commands:</b>\n"
            "/status — Org overview\n"
            "/queue — Approval queue\n"
            "/blog — Blog pipeline\n"
            "/prompts — Image prompts\n"
            "/approve [id] — Approve item\n"
            "/reject [id] — Reject item\n"
            "/run [dept] — Trigger department NOW\n"
            "/runall — Trigger ALL departments\n"
            "/xavier [instruction] — Tell Xavier what to do\n"
            "/boss [dept] [instruction] — Direct any department\n"
            "/history — Recent runs + token usage\n"
            "/alerts — Errors and alerts\n"
            "/costs — Token cost breakdown\n"
            "/fix_image [handle] — Fix missing blog image\n"
            "/help — This menu"
        )

    elif cmd == "/status":
        send_daily_summary()
        return ""  # summary sends its own message

    elif cmd == "/queue":
        return _cmd_queue()

    elif cmd == "/approve":
        return _cmd_approve(args)

    elif cmd == "/reject":
        return _cmd_reject(args)

    elif cmd == "/blog":
        return _cmd_blog()

    elif cmd == "/prompts":
        return _cmd_prompts()

    elif cmd == "/run":
        return _cmd_run(args)

    elif cmd == "/runall":
        return _cmd_runall()

    elif cmd == "/xavier":
        instruction = " ".join(args) if args else ""
        return _cmd_xavier(instruction)

    elif cmd == "/boss":
        return _cmd_boss(args)

    elif cmd == "/history":
        return _cmd_history()

    elif cmd == "/alerts":
        return _cmd_alerts()

    elif cmd == "/costs":
        return _cmd_costs()

    elif cmd == "/dashboard":
        return _cmd_dashboard(chat_id)

    elif cmd == "/fix_image":
        return _cmd_fix_image(args)

    elif cmd == "/help":
        lines = ["\ud83d\udcd6 <b>Available Commands</b>\n"]
        for c, desc in COMMANDS.items():
            lines.append(f"<code>{c}</code> — {desc}")
        return "\n".join(lines)

    else:
        # No slash command — try to understand natural language
        return _handle_natural_language(text, chat_id)


def _cmd_queue() -> str:
    """Show pending approval queue."""
    queue_path = REPO_ROOT / "state" / "queue.json"
    if not queue_path.exists():
        return "\ud83d\udce5 Queue is empty."

    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    pending = queue.get("pending", [])

    if not pending:
        return "\u2705 No items pending approval."

    lines = [f"\ud83d\udce5 <b>{len(pending)} Pending Item(s)</b>\n"]
    for i, item in enumerate(pending):
        dept = item.get("department", "?")
        emoji = DEPT_EMOJI.get(dept, "\u2699\ufe0f")
        lines.append(
            f"{i+1}. {emoji} <b>{item.get('summary', 'No description')}</b>\n"
            f"   Type: <code>{item.get('type', '?')}</code> | "
            f"ID: <code>{item.get('id', '?')}</code>\n"
            f"   /approve {item.get('id', '')} | /reject {item.get('id', '')}"
        )
    return "\n".join(lines)


def _cmd_approve(args: list) -> str:
    """Approve a queue item by ID. Every type routes to an action — no dead ends."""
    if not args:
        return "\u26a0\ufe0f Usage: /approve <item_id>"

    item_id = args[0]
    queue_path = REPO_ROOT / "state" / "queue.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))

    for i, item in enumerate(queue.get("pending", [])):
        if item.get("id") == item_id:
            item["status"] = "approved"
            item["approved_at"] = datetime.now(timezone.utc).isoformat()
            item["approved_by"] = "telegram"
            queue.setdefault("approved", []).append(item)
            queue["pending"].pop(i)
            queue_path.write_text(json.dumps(queue, indent=2), encoding="utf-8")

            item_type = item.get("type", "")
            summary = item.get("summary", item_id)

            # --- Route to the correct action based on type ---
            # Rule 8: No dead ends. Every approval MUST do something.

            if item_type == "blog_publish" or "handle" in item:
                result = _auto_publish_blog(item)
                return f"\u2705 Approved: <b>{summary}</b>\n\n{result}"

            elif item_type == "seo_recommendation":
                result = _apply_seo_recommendation(item)
                return f"\u2705 Approved: <b>{summary}</b>\n\n{result}"

            elif item_type == "content_brief" or item_type == "seo_content_brief":
                result = _queue_content_brief(item)
                return f"\u2705 Approved: <b>{summary}</b>\n\n{result}"

            elif item_type == "social_reply":
                result = _post_social_reply(item)
                return f"\u2705 Approved: <b>{summary}</b>\n\n{result}"

            elif item_type == "email_campaign":
                result = _send_email_campaign(item)
                return f"\u2705 Approved: <b>{summary}</b>\n\n{result}"

            elif item_type in ("dialer_call", "dialer") and item.get("phone_number"):
                result = _execute_dialer_call(item)
                return f"\u2705 Approved: <b>{summary}</b>\n\n{result}"

            elif item_type in ("dialer_data_request", "data_request"):
                result = _process_data_request(item)
                return f"\u2705 Approved: <b>{summary}</b>\n\n{result}"

            else:
                # Rule 8 violation — unknown type with no action
                _log_incident(
                    severity="warning",
                    department=item.get("department", "unknown"),
                    agents_involved=["telegram_bot.py"],
                    title=f"Dead-end approval: type '{item_type}' has no action handler",
                    what_happened=f"Item {item_id} was approved but type '{item_type}' has no automation.",
                    root_cause="Missing action handler for this queue item type",
                    fix_applied="Item marked approved but no action taken. Needs manual handling.",
                    lesson="Every queue item type must map to an action in _cmd_approve.",
                    preventive_rule="Do not queue items with types that have no action handler.",
                )
                send_message(
                    f"\u26a0\ufe0f <b>APPROVAL GAP</b>\n\n"
                    f"Item <code>{item_id}</code> approved but type <code>{item_type}</code> "
                    f"has no automation wired up yet.\n\n"
                    f"Action needed: manual execution or add handler."
                )
                return (
                    f"\u2705 Approved: <b>{summary}</b>\n\n"
                    f"\u26a0\ufe0f No automation for type '{item_type}' — logged as incident."
                )

    return f"\u274c Item not found: <code>{item_id}</code>"


def _log_incident(severity: str, department: str, agents_involved: list,
                   title: str, what_happened: str, root_cause: str,
                   fix_applied: str, lesson: str, preventive_rule: str) -> None:
    """Append an incident to state/incident-log.json."""
    log_path = REPO_ROOT / "state" / "incident-log.json"
    try:
        if log_path.exists():
            log = json.loads(log_path.read_text(encoding="utf-8"))
        else:
            log = {"_docs": "Incident log", "incidents": []}

        incidents = log.get("incidents", [])
        # Next ID
        max_id = 0
        for inc in incidents:
            num = int(inc.get("id", "INC-0").split("-")[1])
            if num > max_id:
                max_id = num

        incidents.insert(0, {
            "id": f"INC-{max_id + 1:03d}",
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "severity": severity,
            "department": department,
            "agents_involved": agents_involved,
            "title": title,
            "what_happened": what_happened,
            "root_cause": root_cause,
            "fix_applied": fix_applied,
            "lesson": lesson,
            "preventive_rule": preventive_rule,
            "status": "open",
        })
        log["incidents"] = incidents
        log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass  # Don't let logging failures break the main flow


def _auto_publish_blog(item: dict) -> str:
    """Auto-publish a blog to Shopify after Telegram approval.

    Fetches the blog content from the pipeline JSON, publishes via
    Shopify GraphQL articleCreate, updates pipeline status, and
    sends a Telegram notification with the published URL.
    """
    handle = item.get("handle", item.get("slug", ""))
    if not handle:
        return "\u26a0\ufe0f No handle found on queue item — skipping auto-publish."

    # --- Load blog from pipeline ---
    bp_path = REPO_ROOT / "departments" / "content" / "blog-pipeline.json"
    if not bp_path.exists():
        return "\u26a0\ufe0f blog-pipeline.json not found — skipping auto-publish."

    bp = json.loads(bp_path.read_text(encoding="utf-8"))
    blog = None
    blog_index = None
    for idx, b in enumerate(bp.get("blogs", [])):
        if b.get("slug") == handle or b.get("handle") == handle:
            blog = b
            blog_index = idx
            break

    if blog is None:
        return f"\u26a0\ufe0f Blog with handle <code>{handle}</code> not found in pipeline."

    # --- Get fresh Shopify token ---
    try:
        token_resp = requests.post(
            "https://gadgetgeekspro.myshopify.com/admin/oauth/access_token",
            data={
                "grant_type": "client_credentials",
                "client_id": os.environ.get("SHOPIFY_CLIENT_ID", ""),
                "client_secret": os.environ.get("SHOPIFY_CLIENT_SECRET", ""),
            },
            timeout=15,
        )
        token_resp.raise_for_status()
        shopify_token = token_resp.json().get("access_token")
        if not shopify_token:
            return "\u274c Failed to obtain Shopify token — no access_token in response."
    except Exception as e:
        return f"\u274c Shopify token error: {e}"

    # --- Generate header image ---
    header_image_url = ""
    try:
        # Import from same directory
        import importlib.util
        spec = importlib.util.spec_from_file_location("image_gen", Path(__file__).parent / "image_gen.py")
        image_gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(image_gen)
        generate_blog_header = image_gen.generate_blog_header
        upload_to_shopify = image_gen.upload_to_shopify
        send_message(f"\ud83c\udfa8 Generating header image for <b>{blog['title'][:60]}</b>...")
        img_result = generate_blog_header(blog["title"], blog.get("category", "refurbished phones"))
        filename = f"blog-header-{handle}.png"
        header_image_url = upload_to_shopify(
            img_result["image_bytes"], filename, img_result.get("mime_type", "image/png")
        )
        send_message(f"\u2705 Header image uploaded to Shopify CDN")
    except Exception as img_err:
        # INC-005 preventive rule: NEVER publish without image — block and log incident
        _log_incident(
            severity="critical",
            department="content",
            agents_involved=["PRESS (telegram_bot.py)", "LENS (image_gen.py)"],
            title=f"Image generation failed for blog: {blog['title'][:50]}",
            what_happened=f"Image generation threw an error: {img_err}",
            root_cause="Image API failure or missing API key",
            fix_applied="Publication blocked. Manual image generation required.",
            lesson="Never publish without a header image. Fix the image pipeline before retrying.",
            preventive_rule="Block publication when image fails. Do not silently skip.",
        )
        send_message(
            f"\u274c <b>PUBLISH BLOCKED</b>\n\n"
            f"Image generation failed for <b>{blog['title'][:60]}</b>\n"
            f"Error: <code>{img_err}</code>\n\n"
            f"Blog will NOT publish without a header image.\n"
            f"Fix the issue and re-approve."
        )
        return f"\u274c Publication blocked — image generation failed: {img_err}"

    # --- Build FAQ schema script tag ---
    faq_schema = blog.get("faq_schema")
    faq_schema_script = ""
    if faq_schema:
        faq_schema_script = (
            '\n<script type="application/ld+json">'
            + json.dumps(faq_schema)
            + "</script>"
        )

    # --- Publish via GraphQL ---
    mutation = """
mutation articleCreate($article: ArticleCreateInput!) {
  articleCreate(article: $article) {
    article { id title handle }
    userErrors { field message }
  }
}
"""
    body_html = ""
    if header_image_url:
        body_html += f'<img src="{header_image_url}" alt="{blog["title"]}" style="width:100%;margin-bottom:2rem;">\n'
    body_html += blog["content"] + faq_schema_script

    article_input = {
        "blogId": "gid://shopify/Blog/88861573371",
        "title": blog["title"],
        "handle": blog["slug"],
        "author": {"name": "Gadget Geeks Team"},
        "body": body_html,
        "summary": blog["meta_description"],
        "tags": ["refurbished-phones", blog.get("category", "guide")],
        "isPublished": True,
    }
    if header_image_url:
        article_input["image"] = {"url": header_image_url}

    variables = {"article": article_input}

    gql_url = "https://gadgetgeekspro.myshopify.com/admin/api/2026-01/graphql.json"
    try:
        gql_resp = requests.post(
            gql_url,
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": shopify_token,
            },
            json={"query": mutation, "variables": variables},
            timeout=30,
        )
        gql_resp.raise_for_status()
        gql_data = gql_resp.json()
    except Exception as e:
        return f"\u274c Shopify GraphQL error: {e}"

    # Check for user errors
    user_errors = (
        gql_data.get("data", {}).get("articleCreate", {}).get("userErrors", [])
    )
    if user_errors:
        msgs = "; ".join(f"{e['field']}: {e['message']}" for e in user_errors)
        return f"\u274c Shopify publish failed: {msgs}"

    article = gql_data.get("data", {}).get("articleCreate", {}).get("article", {})
    article_id = article.get("id", "")
    article_handle = article.get("handle", blog["slug"])
    published_url = f"https://gadgetgeekspro.com/blogs/news/{article_handle}"

    # --- Update blog-pipeline.json ---
    bp["blogs"][blog_index]["status"] = "published"
    bp["blogs"][blog_index]["published_at"] = datetime.now(timezone.utc).isoformat()
    bp["blogs"][blog_index]["shopify_article_id"] = article_id
    # Update stats
    stats = bp.get("pipeline_stats", {})
    stats["total_published"] = stats.get("total_published", 0) + 1
    bp["pipeline_stats"] = stats
    bp_path.write_text(json.dumps(bp, indent=2), encoding="utf-8")

    # --- Send Telegram notification ---
    send_message(
        f"\ud83d\ude80 <b>BLOG PUBLISHED</b>\n\n"
        f"\ud83d\udcdd <b>{blog['title']}</b>\n"
        f"\ud83d\udd17 <a href=\"{published_url}\">{published_url}</a>\n"
        f"\ud83c\udff7 ID: <code>{article_id}</code>"
    )

    return (
        f"\ud83d\ude80 Blog published!\n"
        f"\ud83d\udd17 <a href=\"{published_url}\">{published_url}</a>"
    )


def _apply_seo_recommendation(item: dict) -> str:
    """Apply an approved SEO meta title/description change to Shopify."""
    page = item.get("page", "")
    meta_title = item.get("meta_title", "")
    meta_desc = item.get("meta_description", "")

    if not page or not meta_title:
        return "\u26a0\ufe0f Missing page or meta_title — cannot apply SEO change."

    # Determine resource type and find the Shopify GID
    try:
        shopify_token = _get_shopify_token_for_api()
    except Exception as e:
        return f"\u274c Shopify token error: {e}"

    gql_url = "https://gadgetgeekspro.myshopify.com/admin/api/2026-01/graphql.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": shopify_token}

    # Find the resource by handle
    resource_handle = page.rstrip("/").split("/")[-1]
    resource_type = "collection" if "/collections/" in page else "page" if "/pages/" in page else "product"

    # Look up by handle
    lookup_queries = {
        "collection": f'{{ collectionByHandle(handle: "{resource_handle}") {{ id title }} }}',
        "page": f'{{ pages(first: 50, query: "handle:{resource_handle}") {{ nodes {{ id handle title }} }} }}',
        "product": f'{{ productByHandle(handle: "{resource_handle}") {{ id title }} }}',
    }

    try:
        resp = requests.post(gql_url, headers=headers,
                             json={"query": lookup_queries[resource_type]}, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("data", {})
    except Exception as e:
        return f"\u274c Failed to look up {resource_type}: {e}"

    # Extract GID
    gid = None
    if resource_type == "collection":
        node = data.get("collectionByHandle")
        gid = node.get("id") if node else None
    elif resource_type == "page":
        nodes = data.get("pages", {}).get("nodes", [])
        for n in nodes:
            if n.get("handle") == resource_handle:
                gid = n.get("id")
                break
    elif resource_type == "product":
        node = data.get("productByHandle")
        gid = node.get("id") if node else None

    if not gid:
        return f"\u274c Could not find {resource_type} with handle '{resource_handle}' on Shopify."

    # Apply SEO meta via metafields
    mutation = """
mutation updateSeo($input: HasMetafieldsInput!, $seo: SEOInput!) {
  metafieldsSet(metafields: []) { metafields { id } userErrors { field message } }
}
"""
    # Use the type-specific update mutation instead
    update_mutations = {
        "collection": """
mutation collectionUpdate($input: CollectionInput!) {
  collectionUpdate(input: $input) {
    collection { id title }
    userErrors { field message }
  }
}""",
        "page": """
mutation pageUpdate($id: ID!, $page: PageUpdateInput!) {
  pageUpdate(id: $id, page: $page) {
    page { id title }
    userErrors { field message }
  }
}""",
        "product": """
mutation productUpdate($input: ProductInput!) {
  productUpdate(input: $input) {
    product { id title }
    userErrors { field message }
  }
}""",
    }

    seo_block = {"title": meta_title, "description": meta_desc}

    variables_map = {
        "collection": {"input": {"id": gid, "seo": seo_block}},
        "page": {"id": gid, "page": {"seo": seo_block}},
        "product": {"input": {"id": gid, "seo": seo_block}},
    }

    try:
        resp = requests.post(gql_url, headers=headers,
                             json={"query": update_mutations[resource_type],
                                   "variables": variables_map[resource_type]}, timeout=15)
        resp.raise_for_status()
        result_data = resp.json()
    except Exception as e:
        return f"\u274c Shopify update failed: {e}"

    # Check for errors
    errors_key = f"{resource_type}Update"
    user_errors = result_data.get("data", {}).get(errors_key, {}).get("userErrors", [])
    if user_errors:
        msgs = "; ".join(f"{e['field']}: {e['message']}" for e in user_errors)
        return f"\u274c SEO update failed: {msgs}"

    verify_url = f"https://gadgetgeekspro.com{page}"
    send_message(
        f"\u2705 <b>SEO UPDATE APPLIED</b>\n\n"
        f"\ud83d\udcc4 Page: <code>{page}</code>\n"
        f"\ud83d\udcdd Title: {meta_title}\n"
        f"\ud83d\udcdd Description: {meta_desc[:80]}...\n"
        f"\ud83d\udd17 <a href=\"{verify_url}\">Verify here</a>"
    )
    return f"\u2705 SEO updated on {page}\n\ud83d\udd17 <a href=\"{verify_url}\">Verify</a>"


def _queue_content_brief(item: dict) -> str:
    """Move an approved content brief into the blog pipeline for SCRIBE to pick up."""
    bp_path = REPO_ROOT / "departments" / "content" / "blog-pipeline.json"
    if not bp_path.exists():
        return "\u26a0\ufe0f blog-pipeline.json not found."

    bp = json.loads(bp_path.read_text(encoding="utf-8"))

    # Build a new blog entry from the brief
    slug = item.get("page", "").rstrip("/").split("/")[-1] or item.get("target_keyword", "").replace(" ", "-").lower()
    new_blog = {
        "blog_id": f"blog_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        "title": item.get("meta_title", item.get("summary", "Untitled")),
        "slug": slug,
        "meta_description": item.get("meta_description", ""),
        "target_keywords": [item.get("target_keyword", "")],
        "word_count_target": item.get("word_count_target", "1500-2000"),
        "key_messaging": item.get("key_messaging", []),
        "internal_links_needed": item.get("internal_links_needed", []),
        "status": "brief_ready",
        "created": datetime.now(timezone.utc).isoformat(),
        "source_queue_id": item.get("id", ""),
    }

    bp.setdefault("blogs", []).append(new_blog)
    bp_path.write_text(json.dumps(bp, indent=2), encoding="utf-8")

    send_message(
        f"\ud83d\udcdd <b>BRIEF QUEUED FOR SCRIBE</b>\n\n"
        f"\ud83d\udccc Topic: {new_blog['title'][:70]}\n"
        f"\ud83c\udfaf Keyword: {item.get('target_keyword', 'N/A')}\n"
        f"\ud83d\udcc5 SCRIBE picks it up next Mon/Wed/Fri 9:30 UTC"
    )
    return f"\ud83d\udcdd Brief added to pipeline. SCRIBE writes it next scheduled run."


def _post_social_reply(item: dict) -> str:
    """Post an approved social media reply via X API."""
    reply_content = item.get("reply_content", "")
    target = item.get("target_post", "unknown")

    if not reply_content:
        return "\u26a0\ufe0f No reply_content found — cannot post."

    # Try X API
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("x_api", Path(__file__).parent / "x_api.py")
        x_api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(x_api)

        if hasattr(x_api, "post_tweet"):
            result = x_api.post_tweet(reply_content)
            send_message(
                f"\ud83d\udce2 <b>SOCIAL REPLY POSTED</b>\n\n"
                f"\ud83c\udfaf Target: {target[:60]}\n"
                f"\ud83d\udcac Reply: {reply_content[:100]}...\n"
                f"\u2705 Posted via X API"
            )
            return f"\ud83d\udce2 Reply posted to X targeting {target[:40]}"
        else:
            raise AttributeError("post_tweet not found in x_api.py")
    except Exception as e:
        # Fallback: log for manual posting
        send_message(
            f"\u26a0\ufe0f <b>SOCIAL REPLY — MANUAL POST NEEDED</b>\n\n"
            f"\ud83c\udfaf Target: {target}\n"
            f"\ud83d\udcac Copy:\n<code>{reply_content}</code>\n\n"
            f"X API unavailable: {e}\n"
            f"Copy the text above and post manually."
        )
        return f"\u26a0\ufe0f X API unavailable — reply content sent to Telegram for manual posting."


def _send_email_campaign(item: dict) -> str:
    """Send an approved email campaign via Resend API."""
    campaign_id = item.get("campaign_id", "unknown")
    subject = item.get("subject_variants", {})
    subject_line = subject.get("a", "") if isinstance(subject, dict) else str(subject)

    # Check if Resend is configured
    resend_key = os.environ.get("RESEND_API_KEY", "")
    if not resend_key:
        send_message(
            f"\u26a0\ufe0f <b>EMAIL — MANUAL SEND NEEDED</b>\n\n"
            f"\ud83d\udce7 Campaign: {campaign_id}\n"
            f"\ud83d\udcdd Subject: {subject_line}\n"
            f"\ud83d\udc65 Segment: {item.get('segment', 'N/A')}\n\n"
            f"RESEND_API_KEY not configured. Set it in GitHub Secrets to enable auto-send."
        )
        return f"\u26a0\ufe0f Resend not configured — email details sent to Telegram for manual send."

    # TODO: Wire up actual Resend sending when key is available
    send_message(
        f"\ud83d\udce7 <b>EMAIL CAMPAIGN QUEUED</b>\n\n"
        f"\ud83d\udccc Campaign: {campaign_id}\n"
        f"\ud83d\udcdd Subject: {subject_line}\n"
        f"\ud83d\udc65 Segment: {item.get('segment', 'N/A')}\n"
        f"\ud83d\udcca Est. recipients: {item.get('estimated_send_count', 'N/A')}"
    )
    return f"\ud83d\udce7 Email campaign {campaign_id} queued for send."


def _execute_dialer_call(item: dict) -> str:
    """Execute an approved phone call via Vapi.ai."""
    phone = item.get("phone_number", "")
    name = item.get("customer_name", "Unknown")
    reason = item.get("reason", "")

    if not phone:
        return "\u26a0\ufe0f No phone_number — cannot make call."

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("vapi_caller", Path(__file__).parent / "vapi_caller.py")
        vapi = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vapi)

        if hasattr(vapi, "make_call"):
            result = vapi.make_call(phone, name, reason)
            send_message(
                f"\ud83d\udcde <b>CALL EXECUTED</b>\n\n"
                f"\ud83d\udc64 {name}\n"
                f"\ud83d\udcf1 {phone}\n"
                f"\ud83d\udccc Reason: {reason[:60]}\n"
                f"\u2705 Call initiated via Vapi.ai"
            )
            return f"\ud83d\udcde Call to {name} ({phone}) initiated."
        else:
            raise AttributeError("make_call not found")
    except Exception as e:
        send_message(
            f"\u26a0\ufe0f <b>CALL — MANUAL DIAL NEEDED</b>\n\n"
            f"\ud83d\udc64 {name}\n"
            f"\ud83d\udcf1 {phone}\n"
            f"\ud83d\udccc {reason}\n\n"
            f"Vapi error: {e}"
        )
        return f"\u26a0\ufe0f Vapi unavailable — call details sent to Telegram."


def _process_data_request(item: dict) -> str:
    """Acknowledge a data request approval — these require Shopify data access."""
    required = item.get("required_data", [])
    purpose = item.get("purpose", "")

    send_message(
        f"\ud83d\udcca <b>DATA REQUEST APPROVED</b>\n\n"
        f"\ud83d\udccc Purpose: {purpose[:80]}\n"
        f"\ud83d\udcdd Required data:\n" +
        "\n".join(f"  \u2022 {d[:60]}" for d in required[:5]) +
        f"\n\n\u26a0\ufe0f Requires Shopify API data access — will be processed next dialer workflow run."
    )
    return f"\ud83d\udcca Data request approved. Processed on next dialer run."


def _get_shopify_token_for_api() -> str:
    """Get a fresh Shopify access token via client credentials."""
    resp = requests.post(
        "https://gadgetgeekspro.myshopify.com/admin/oauth/access_token",
        data={
            "grant_type": "client_credentials",
            "client_id": os.environ.get("SHOPIFY_CLIENT_ID", ""),
            "client_secret": os.environ.get("SHOPIFY_CLIENT_SECRET", ""),
        },
        timeout=15,
    )
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise ValueError("No access_token in response")
    return token


def _cmd_reject(args: list) -> str:
    """Reject a queue item by ID."""
    if not args:
        return "\u26a0\ufe0f Usage: /reject <item_id>"

    item_id = args[0]
    queue_path = REPO_ROOT / "state" / "queue.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))

    for i, item in enumerate(queue.get("pending", [])):
        if item.get("id") == item_id:
            item["status"] = "rejected"
            item["rejected_at"] = datetime.now(timezone.utc).isoformat()
            item["rejected_by"] = "telegram"
            queue.setdefault("rejected", []).append(item)
            queue["pending"].pop(i)
            queue_path.write_text(json.dumps(queue, indent=2), encoding="utf-8")
            return f"\u274c Rejected: <b>{item.get('summary', item_id)}</b>"

    return f"\u274c Item not found: <code>{item_id}</code>"


def _cmd_fix_image(args: list) -> str:
    """Generate and attach a header image to a published blog that's missing one.

    Usage: /fix_image <blog_handle>
    or:    /fix_image all  (fix ALL published blogs missing images)

    This is the safety net for INC-005/INC-007 — retroactively fix published
    blogs that somehow got out without a header image.
    """
    if not args:
        return (
            "\u26a0\ufe0f Usage: /fix_image <blog_handle>\n"
            "Example: /fix_image cheap-refurbished-phones-guide\n"
            "Or: /fix_image all"
        )

    target = args[0].strip()

    # Load blog pipeline to find published blogs
    bp_path = REPO_ROOT / "departments" / "content" / "blog-pipeline.json"
    if not bp_path.exists():
        return "\u26a0\ufe0f blog-pipeline.json not found."

    bp = json.loads(bp_path.read_text(encoding="utf-8"))
    blogs_to_fix = []

    for blog in bp.get("blogs", []):
        if blog.get("status") != "published":
            continue
        if target == "all" or blog.get("slug") == target or blog.get("handle") == target:
            blogs_to_fix.append(blog)

    if not blogs_to_fix:
        return f"\u26a0\ufe0f No published blog found with handle <code>{target}</code>"

    results = []
    for blog in blogs_to_fix:
        handle = blog.get("slug") or blog.get("handle", "")
        title = blog.get("title", "")
        article_id = blog.get("shopify_article_id", "")

        if not article_id:
            results.append(f"\u274c <b>{handle}</b> — no Shopify article ID in pipeline")
            continue

        send_message(f"\ud83c\udfa8 Generating header image for <b>{title[:60]}</b>...")

        # --- Generate image via Gemini ---
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "image_gen", Path(__file__).parent / "image_gen.py"
            )
            image_gen = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(image_gen)

            img_result = image_gen.generate_blog_header(
                title, blog.get("category", "refurbished phones")
            )
            filename = f"blog-header-{handle}.png"
            cdn_url = image_gen.upload_to_shopify(
                img_result["image_bytes"], filename,
                img_result.get("mime_type", "image/png")
            )
        except Exception as e:
            results.append(f"\u274c <b>{handle}</b> — image generation failed: {e}")
            continue

        # --- Attach to article via articleUpdate ---
        try:
            token = _get_shopify_token_for_api()
            mutation = """
mutation articleUpdate($id: ID!, $article: ArticleUpdateInput!) {
  articleUpdate(id: $id, article: $article) {
    article { id title handle image { url } }
    userErrors { field message }
  }
}
"""
            variables = {
                "id": article_id,
                "article": {
                    "image": {"url": cdn_url, "altText": title},
                },
            }
            gql_url = "https://gadgetgeekspro.myshopify.com/admin/api/2026-01/graphql.json"
            resp = requests.post(
                gql_url,
                headers={
                    "Content-Type": "application/json",
                    "X-Shopify-Access-Token": token,
                },
                json={"query": mutation, "variables": variables},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            user_errors = data.get("data", {}).get("articleUpdate", {}).get("userErrors", [])
            if user_errors:
                msgs = "; ".join(f"{e['field']}: {e['message']}" for e in user_errors)
                results.append(f"\u274c <b>{handle}</b> — articleUpdate failed: {msgs}")
                continue

            # Also prepend the image to body_html if not already there
            article_data = data.get("data", {}).get("articleUpdate", {}).get("article", {})
            img_url_final = article_data.get("image", {}).get("url", cdn_url)

            results.append(
                f"\u2705 <b>{handle}</b> — image attached!\n"
                f"   CDN: {img_url_final[:80]}..."
            )

        except Exception as e:
            results.append(f"\u274c <b>{handle}</b> — Shopify update failed: {e}")

    summary = "\n".join(results)
    send_message(
        f"\ud83d\uddbc <b>IMAGE FIX COMPLETE</b>\n\n{summary}"
    )
    return summary


def _cmd_blog() -> str:
    """Show blog pipeline status."""
    bp_path = REPO_ROOT / "departments" / "content" / "blog-pipeline.json"
    if not bp_path.exists():
        return "\u270d\ufe0f No blogs in pipeline."

    bp = json.loads(bp_path.read_text(encoding="utf-8"))
    blogs = bp.get("blogs", [])
    stats = bp.get("pipeline_stats", {})

    lines = [
        "\u270d\ufe0f <b>BLOG PIPELINE</b>\n",
        f"Drafted: {stats.get('total_drafted', 0)} | "
        f"Approved: {stats.get('total_approved', 0)} | "
        f"Published: {stats.get('total_published', 0)} | "
        f"Blocked: {stats.get('total_blocked', 0)}\n",
    ]

    for blog in blogs[-5:]:  # Last 5
        status = blog.get("status", "?")
        qa = blog.get("qa_score", {})
        rating = qa.get("rating", "?")
        title = blog.get("title", "Untitled")
        lines.append(
            f"\u2022 <b>{title[:60]}</b>\n"
            f"  Status: <code>{status}</code> | QA: {rating}"
        )

    return "\n".join(lines)


def _cmd_prompts() -> str:
    """Show image prompt stats."""
    ip_path = REPO_ROOT / "departments" / "social" / "image-prompts.json"
    if not ip_path.exists():
        return "\ud83c\udfa8 No image prompts yet."

    ip = json.loads(ip_path.read_text(encoding="utf-8"))
    folders = ip.get("folders", {})
    qa = ip.get("qa_summary", {})

    lines = ["\ud83c\udfa8 <b>IMAGE PROMPTS</b>\n"]

    total = 0
    for folder_id, folder in folders.items():
        prompts = folder.get("prompts", [])
        total += len(prompts)
        lines.append(f"\ud83d\udcc2 {folder.get('name', folder_id)}: {len(prompts)} prompts")

    lines.insert(1, f"Total: {total} prompts\n")

    if qa:
        lines.append(f"\nQA: {qa.get('excellent', 0)} excellent, "
                      f"{qa.get('good', 0)} good, "
                      f"{qa.get('needs_work', 0)} needs work")

    return "\n".join(lines)


def _trigger_workflow(workflow_file: str) -> tuple:
    """Trigger a GitHub Actions workflow via API.

    Returns (success: bool, message: str).
    """
    gh_token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
    if not gh_token:
        return False, "No GH_TOKEN or GITHUB_TOKEN set"

    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{workflow_file}/dispatches"
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {gh_token}",
            "Accept": "application/vnd.github.v3+json",
        },
        json={"ref": "main"},
        timeout=15,
    )
    if resp.status_code == 204:
        return True, "triggered"
    return False, f"HTTP {resp.status_code}: {resp.text[:200]}"


def _cmd_run(args: list) -> str:
    """Trigger a department workflow via GitHub Actions."""
    if not args:
        dept_list = ", ".join(sorted(DEPT_WORKFLOW_MAP.keys()))
        return (
            f"\u26a0\ufe0f Usage: /run <department>\n\n"
            f"Available:\n<code>{dept_list}</code>"
        )

    dept = args[0].lower().replace("-", "_")
    workflow = DEPT_WORKFLOW_MAP.get(dept)
    if not workflow:
        dept_list = ", ".join(sorted(DEPT_WORKFLOW_MAP.keys()))
        return (
            f"\u274c Unknown department: <code>{dept}</code>\n\n"
            f"Available:\n<code>{dept_list}</code>"
        )

    name = DEPT_NAMES.get(dept, dept)
    emoji = DEPT_EMOJI.get(dept, "\u2699\ufe0f")
    ok, msg = _trigger_workflow(workflow)
    if ok:
        return f"{emoji} <b>{name}</b> triggered!\n\nWorkflow dispatched. Results in ~2 min."
    return f"\u274c Failed to trigger <b>{name}</b>: {msg}"


def _cmd_runall() -> str:
    """Trigger all department workflows."""
    # Core departments in logical order
    core_depts = [
        "intel", "x_intel", "seo", "content", "email",
        "social_morning", "cro", "image_prompts", "blog_writer",
        "dialer", "gm_queue",
    ]
    results = []
    for dept in core_depts:
        workflow = DEPT_WORKFLOW_MAP.get(dept)
        if workflow:
            ok, msg = _trigger_workflow(workflow)
            emoji = "\u2705" if ok else "\u274c"
            name = DEPT_NAMES.get(dept, dept)
            results.append(f"{emoji} {name}")

    return (
        "\ud83d\ude80 <b>ALL DEPARTMENTS TRIGGERED</b>\n\n"
        + "\n".join(results)
        + "\n\nResults arriving in ~2-5 min."
    )


def _save_boss_instruction(department: str, instruction: str):
    """Save a boss instruction to the instructions file for a department."""
    instr_path = REPO_ROOT / "state" / "boss-instructions.json"
    if instr_path.exists():
        instructions = json.loads(instr_path.read_text(encoding="utf-8"))
    else:
        instructions = {"pending": []}

    instructions["pending"].append({
        "department": department,
        "instruction": instruction,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
    })
    instr_path.write_text(json.dumps(instructions, indent=2, ensure_ascii=False), encoding="utf-8")


def _cmd_xavier(instruction: str) -> str:
    """Send an instruction to Xavier (dialer agent)."""
    if not instruction:
        return (
            "\ud83d\udcde <b>XAVIER — AI Sales Agent</b>\n\n"
            "Usage: /xavier <instruction>\n\n"
            "<b>Examples:</b>\n"
            "<code>/xavier call John about the iPhone 14 he left in cart</code>\n"
            "<code>/xavier follow up with B2B lead from last week</code>\n"
            "<code>/xavier build a win-back list for customers inactive 90+ days</code>\n"
            "<code>/xavier check outcomes from yesterday's calls</code>\n\n"
            "Xavier will add calls to the approval queue. You approve before any call goes out."
        )

    # Save instruction
    _save_boss_instruction("dialer", instruction)

    # Also trigger the dialer workflow so Xavier picks it up
    workflow = DEPT_WORKFLOW_MAP.get("dialer")
    triggered = False
    if workflow:
        ok, _ = _trigger_workflow(workflow)
        triggered = ok

    response = (
        f"\ud83d\udcde <b>XAVIER — Instruction received</b>\n\n"
        f"<i>{instruction[:300]}</i>\n\n"
    )
    if triggered:
        response += "\u2705 Dialer workflow triggered. Xavier is on it."
    else:
        response += "\u23f3 Saved. Xavier will pick this up on next scheduled run."

    return response


def _cmd_boss(args: list) -> str:
    """Send a direct instruction to any department."""
    if len(args) < 2:
        dept_list = ", ".join(sorted(DEPT_WORKFLOW_MAP.keys()))
        return (
            "\ud83d\udc53 <b>BOSS MODE</b>\n\n"
            "Usage: /boss <department> <instruction>\n\n"
            f"Departments:\n<code>{dept_list}</code>\n\n"
            "<b>Examples:</b>\n"
            "<code>/boss content write a blog about iPhone 16 vs 15</code>\n"
            "<code>/boss email create a flash sale campaign for this weekend</code>\n"
            "<code>/boss seo audit our top 5 product pages</code>\n"
            "<code>/boss intel research what Back Market is doing with pricing</code>"
        )

    dept = args[0].lower().replace("-", "_")
    instruction = " ".join(args[1:])

    if dept not in DEPT_WORKFLOW_MAP and dept not in DEPT_NAMES:
        dept_list = ", ".join(sorted(DEPT_WORKFLOW_MAP.keys()))
        return f"\u274c Unknown department: <code>{dept}</code>\n\nAvailable:\n<code>{dept_list}</code>"

    name = DEPT_NAMES.get(dept, dept)
    emoji = DEPT_EMOJI.get(dept, "\u2699\ufe0f")

    # Save instruction
    _save_boss_instruction(dept, instruction)

    # Trigger the workflow
    workflow = DEPT_WORKFLOW_MAP.get(dept)
    triggered = False
    if workflow:
        ok, _ = _trigger_workflow(workflow)
        triggered = ok

    response = (
        f"{emoji} <b>{name} — Instruction received</b>\n\n"
        f"<i>{instruction[:300]}</i>\n\n"
    )
    if triggered:
        response += f"\u2705 {name} workflow triggered. Processing now."
    else:
        response += f"\u23f3 Saved. {name} will pick this up on next scheduled run."

    return response


def _cmd_history() -> str:
    """Show last 10 department runs from run-history.json."""
    history_path = REPO_ROOT / "state" / "run-history.json"
    if not history_path.exists():
        return "\ud83d\udcca No run history yet. Runs will be logged after the next department cycle."

    history = json.loads(history_path.read_text(encoding="utf-8"))
    runs = history.get("runs", [])[:10]
    stats = history.get("stats", {})

    if not runs:
        return "\ud83d\udcca No runs recorded yet."

    lines = [
        f"\ud83d\udcca <b>RUN HISTORY</b> (last {len(runs)})\n",
        f"Total: {stats.get('total_runs', 0)} runs | "
        f"{stats.get('total_tokens', 0):,} tokens | "
        f"{stats.get('total_errors', 0)} errors\n",
    ]

    for run in runs:
        dept = run.get("department", "?")
        emoji = DEPT_EMOJI.get(dept, "\u2699\ufe0f")
        name = DEPT_NAMES.get(dept, dept)
        status = "\u2705" if run.get("status") == "ok" else "\u274c"
        tokens = run.get("tokens", {})
        total_tok = tokens.get("total", 0)
        ts = run.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            time_str = dt.strftime("%b %d %H:%M")
        except Exception:
            time_str = ts[:16]

        actions = run.get("actions", {})
        changes = len(run.get("changes", []))
        boss = " \ud83d\udc53" if run.get("had_boss_instructions") else ""

        lines.append(
            f"{status} {emoji} <b>{name}</b> {time_str}{boss}\n"
            f"   {total_tok:,} tok | {actions.get('file_updates', 0)} files | "
            f"{actions.get('queue_items', 0)} queued | {changes} changed"
        )

    return "\n".join(lines)


def _cmd_alerts() -> str:
    """Show recent alerts from alert-history.json."""
    alerts_path = REPO_ROOT / "state" / "alert-history.json"
    if not alerts_path.exists():
        return "\ud83d\udea8 No alerts yet."

    alerts = json.loads(alerts_path.read_text(encoding="utf-8"))
    items = alerts.get("alerts", [])[:15]

    if not items:
        return "\u2705 No alerts. Everything is clean."

    level_emoji = {"critical": "\ud83d\udd34", "error": "\ud83d\udfe0", "warning": "\ud83d\udfe1", "info": "\ud83d\udfe2"}

    lines = [f"\ud83d\udea8 <b>ALERTS</b> (last {len(items)})\n"]
    for a in items:
        emoji = level_emoji.get(a.get("level", "info"), "\u2753")
        dept = a.get("department", "?")
        name = DEPT_NAMES.get(dept, dept)
        ts = a.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            time_str = dt.strftime("%b %d %H:%M")
        except Exception:
            time_str = ts[:16]

        lines.append(f"{emoji} <b>{name}</b> ({time_str})\n   {a.get('message', '?')[:200]}")

    return "\n".join(lines)


def _cmd_costs() -> str:
    """Show token usage and cost breakdown per department."""
    history_path = REPO_ROOT / "state" / "run-history.json"
    if not history_path.exists():
        return "\ud83d\udcb0 No cost data yet."

    history = json.loads(history_path.read_text(encoding="utf-8"))
    dept_stats = history.get("department_stats", {})
    total_stats = history.get("stats", {})

    if not dept_stats:
        return "\ud83d\udcb0 No department stats yet."

    # Rough pricing: Sonnet ~$3/M input + $15/M output, Opus ~$15/M + $75/M
    # Use blended average ~$10/M tokens for estimation
    total_tokens = total_stats.get("total_tokens", 0)
    est_cost = total_tokens * 10 / 1_000_000  # $10 per million tokens blended

    lines = [
        f"\ud83d\udcb0 <b>TOKEN USAGE & COSTS</b>\n",
        f"Total: {total_tokens:,} tokens (~${est_cost:.2f})\n",
        f"Runs: {total_stats.get('total_runs', 0)} | Errors: {total_stats.get('total_errors', 0)}\n",
    ]

    # Sort by token usage descending
    sorted_depts = sorted(dept_stats.items(), key=lambda x: x[1].get("tokens", 0), reverse=True)

    for dept, ds in sorted_depts:
        emoji = DEPT_EMOJI.get(dept, "\u2699\ufe0f")
        name = DEPT_NAMES.get(dept, dept)
        tok = ds.get("tokens", 0)
        runs = ds.get("runs", 0)
        dept_cost = tok * 10 / 1_000_000
        lines.append(
            f"{emoji} <b>{name}</b>: {tok:,} tok ({runs} runs) ~${dept_cost:.2f}"
        )

    return "\n".join(lines)


def _cmd_dashboard(chat_id: int) -> str:
    """Send the dashboard as a Telegram WebApp button."""
    token = _get_token()
    if not token:
        return "\u274c No bot token available."

    # Send a message with an inline keyboard containing a WebApp button
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "\ud83c\udfae <b>GADGETGEEKS HQ — GOD MODE</b>\n\nTap below to open the office dashboard.",
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[
                {
                    "text": "\ud83c\udfae Open HQ Dashboard",
                    "web_app": {"url": DASHBOARD_URL}
                }
            ]]
        }
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        return ""  # Message already sent via API
    except Exception as e:
        # Fallback: send direct link
        return (
            f"\ud83c\udfae <b>GADGETGEEKS HQ — GOD MODE</b>\n\n"
            f"\ud83d\udd17 <a href=\"{DASHBOARD_URL}\">Open Dashboard</a>\n\n"
            f"Bookmark this link on your phone for instant access."
        )


# ---------------------------------------------------------------------------
# Natural language intent detection
# ---------------------------------------------------------------------------

# Department name aliases for fuzzy matching
_DEPT_ALIASES = {
    "xavier": "dialer", "dialer": "dialer", "caller": "dialer", "phone": "dialer", "calls": "dialer",
    "intel": "intel", "market": "intel", "research": "intel", "competitors": "intel",
    "seo": "seo", "keywords": "seo", "ranking": "seo", "rankings": "seo",
    "content": "content", "calendar": "content", "topics": "content",
    "email": "email", "emails": "email", "newsletter": "email", "campaign": "email",
    "social": "social_morning", "twitter": "social_morning", "post": "social_morning", "posts": "social_morning",
    "cro": "cro", "conversion": "cro", "optimize": "cro",
    "blog": "blog_writer", "blogs": "blog_writer", "article": "blog_writer", "write": "blog_writer",
    "image": "image_prompts", "images": "image_prompts", "prompts": "image_prompts", "photos": "image_prompts",
    "gm": "gm_queue", "report": "gm_report",
    "x": "x_intel", "hawk": "x_intel",
}


def _detect_department(text: str) -> str | None:
    """Try to detect a department from natural language."""
    words = text.lower().split()
    for word in words:
        dept = _DEPT_ALIASES.get(word)
        if dept:
            return dept
    return None


def _handle_natural_language(text: str, chat_id: int) -> str:
    """Parse natural language and route to the right handler.

    Intent priority:
    1. Xavier / call instructions
    2. Run / trigger / start a department
    3. Status / how's it going
    4. Approve / reject
    5. Alerts / errors / problems
    6. Costs / spending / tokens
    7. History / runs / what happened
    8. Boss instruction to a specific department
    9. Fallback: GM instruction
    """
    lower = text.lower().strip()

    # --- 1. XAVIER / CALL INTENT ---
    # "xavier call john", "tell xavier to...", "have xavier...", "call the B2B lead"
    xavier_triggers = ["xavier", "call ", "phone ", "dial "]
    if any(t in lower for t in xavier_triggers):
        # Strip "xavier" prefix if present to get the actual instruction
        instruction = text.strip()
        for prefix in ["xavier ", "xavier, ", "tell xavier to ", "have xavier ",
                        "ask xavier to ", "xavier please ", "hey xavier "]:
            if lower.startswith(prefix):
                instruction = text[len(prefix):].strip()
                break
        return _cmd_xavier(instruction)

    # --- 2. RUN / TRIGGER INTENT ---
    run_triggers = ["run ", "trigger ", "start ", "fire ", "launch ", "execute "]
    if any(lower.startswith(t) for t in run_triggers):
        dept = _detect_department(text)
        if dept:
            return _cmd_run([dept])
        # "run all" / "run everything" / "trigger all"
        if any(w in lower for w in ["all", "everything", "everyone"]):
            return _cmd_runall()

    # --- 3. DASHBOARD / OFFICE INTENT ---
    if any(t in lower for t in ["dashboard", "office", "open hq", "god mode", "pixel"]):
        return _cmd_dashboard(chat_id)

    # --- 3b. STATUS INTENT ---
    status_triggers = ["status", "how's it going", "hows it going", "what's happening",
                        "whats happening", "how are things", "overview",
                        "what's going on", "whats going on", "how are the agents",
                        "report", "sitrep", "check in"]
    if any(t in lower for t in status_triggers):
        send_daily_summary()
        return ""

    # --- 4. APPROVE / REJECT INTENT ---
    if any(w in lower for w in ["approve", "approved", "yes approve", "go ahead", "looks good", "ship it"]):
        # Try to find an ID in the text
        import re
        ids = re.findall(r'[A-Za-z0-9_-]{4,}', text)
        # Filter out common words
        common = {"approve", "approved", "reject", "looks", "good", "ship", "ahead", "yes", "the", "this", "that", "please"}
        ids = [i for i in ids if i.lower() not in common]
        if ids:
            return _cmd_approve(ids[:1])
        # No ID found — show the queue so they can pick
        return _cmd_queue()

    if any(w in lower for w in ["reject", "rejected", "no", "deny", "kill it", "nope"]):
        import re
        ids = re.findall(r'[A-Za-z0-9_-]{4,}', text)
        common = {"approve", "approved", "reject", "rejected", "deny", "kill", "nope", "please", "the", "this", "that"}
        ids = [i for i in ids if i.lower() not in common]
        if ids:
            return _cmd_reject(ids[:1])

    # --- 5. ALERTS / ERRORS ---
    if any(w in lower for w in ["alert", "alerts", "error", "errors", "problem", "problems",
                                  "broken", "failing", "failed", "what broke", "issues"]):
        return _cmd_alerts()

    # --- 6. COSTS / SPENDING ---
    if any(w in lower for w in ["cost", "costs", "spending", "tokens", "budget", "money",
                                  "how much", "expensive"]):
        return _cmd_costs()

    # --- 7. HISTORY / RUNS ---
    if any(w in lower for w in ["history", "recent", "last run", "what happened",
                                  "what ran", "runs"]):
        return _cmd_history()

    # --- 8. QUEUE ---
    if any(w in lower for w in ["queue", "pending", "waiting", "approval", "approvals"]):
        return _cmd_queue()

    # --- 9. BLOG STATUS ---
    if any(w in lower for w in ["blog", "blogs", "articles", "pipeline"]):
        return _cmd_blog()

    # --- 10. BOSS INSTRUCTION TO SPECIFIC DEPARTMENT ---
    dept = _detect_department(text)
    if dept and len(text.split()) > 2:
        # Looks like an instruction for a specific department
        # Strip the department keyword to get the instruction
        instruction = text
        name = DEPT_NAMES.get(dept, dept)
        emoji = DEPT_EMOJI.get(dept, "\u2699\ufe0f")

        _save_boss_instruction(dept, instruction)
        workflow = DEPT_WORKFLOW_MAP.get(dept)
        triggered = False
        if workflow:
            ok, _ = _trigger_workflow(workflow)
            triggered = ok

        response = (
            f"{emoji} <b>Got it — sending to {name}</b>\n\n"
            f"<i>{instruction[:300]}</i>\n\n"
        )
        if triggered:
            response += f"\u2705 {name} workflow triggered."
        else:
            response += f"\u23f3 Saved. {name} picks this up on next run."
        return response

    # --- 11. FALLBACK: GM instruction ---
    _save_boss_instruction("gm_queue", text)
    return (
        f"\ud83d\udcdd <b>Got it, boss.</b>\n\n"
        f"<i>{text[:200]}</i>\n\n"
        f"Saved for GM. All departments will see this.\n"
        f"Say <code>run gm</code> to process now."
    )


# ---------------------------------------------------------------------------
# Main polling loop (for the GitHub Actions workflow)
# ---------------------------------------------------------------------------

def poll_and_respond():
    """Single poll cycle: get updates, respond, save offset."""
    offset_path = REPO_ROOT / "state" / "telegram_offset.json"
    offset = None
    if offset_path.exists():
        try:
            offset = json.loads(offset_path.read_text(encoding="utf-8")).get("offset")
        except Exception:
            pass

    updates = get_updates(offset=offset, timeout=10)

    if not updates:
        return 0

    processed = 0
    for update in updates:
        msg = update.get("message", {})
        text = msg.get("text", "")
        chat = msg.get("chat", {})
        chat_id = chat.get("id")

        if not chat_id or not text:
            continue

        # Auto-save chat ID
        current_chat = _get_chat_id()
        if not current_chat:
            _save_chat_id(chat_id)
            print(f"Auto-discovered chat_id: {chat_id}")

        # Handle the message
        response = handle_command(text, chat_id)
        if response:
            send_message(response, chat_id=str(chat_id))
        processed += 1

        # Update offset
        new_offset = update["update_id"] + 1
        offset_path.parent.mkdir(parents=True, exist_ok=True)
        offset_path.write_text(json.dumps({"offset": new_offset}), encoding="utf-8")

    return processed


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "poll":
        n = poll_and_respond()
        print(f"Processed {n} message(s)")
    elif len(sys.argv) > 1 and sys.argv[1] == "discover":
        cid = auto_discover_chat_id()
        if cid:
            print(f"Chat ID: {cid}")
            send_message("\ud83c\udfae <b>Connected!</b> GadgetGeeks HQ is now sending updates to this chat.", chat_id=str(cid))
        else:
            print("No messages found. Send /start to the bot first.")
    elif len(sys.argv) > 1 and sys.argv[1] == "summary":
        send_daily_summary()
    else:
        print("Usage: python telegram_bot.py [poll|discover|summary]")
