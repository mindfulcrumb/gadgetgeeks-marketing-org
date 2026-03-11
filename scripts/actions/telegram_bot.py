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

    send_message(
        f"\ud83d\udce5 <b>NEW APPROVAL NEEDED</b>\n\n"
        f"{emoji} From: <b>{DEPT_NAMES.get(dept, dept)}</b>\n"
        f"\ud83c\udff7 Type: <code>{item_type}</code>\n"
        f"\ud83d\udcdd {summary}\n\n"
        f"Reply /approve or /reject"
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
    "/run": "Manually trigger a department",
    "/blog": "Show blog pipeline status",
    "/prompts": "Show image prompt stats",
    "/help": "Show available commands",
}


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
            "I'll send you real-time updates from all 13 agents.\n\n"
            "Commands:\n"
            "/status — Org overview\n"
            "/queue — Approval queue\n"
            "/blog — Blog pipeline\n"
            "/prompts — Image prompts\n"
            "/approve [id] — Approve item\n"
            "/reject [id] — Reject item\n"
            "/run [dept] — Trigger department\n"
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

    elif cmd == "/help":
        lines = ["\ud83d\udcd6 <b>Available Commands</b>\n"]
        for c, desc in COMMANDS.items():
            lines.append(f"<code>{c}</code> — {desc}")
        return "\n".join(lines)

    else:
        # Not a command — could be a natural language message to the GM
        return (
            f"\ud83e\udd16 I received your message. "
            f"Use /help to see commands, or wait for the next GM queue run "
            f"to process your request.\n\n"
            f"<i>Your message: {text[:200]}</i>"
        )


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
    """Approve a queue item by ID."""
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

            # Auto-publish if this is a blog item
            if item.get("type") == "blog_publish" or "handle" in item:
                publish_result = _auto_publish_blog(item)
                return (
                    f"\u2705 Approved: <b>{item.get('summary', item_id)}</b>\n\n"
                    f"{publish_result}"
                )

            return f"\u2705 Approved: <b>{item.get('summary', item_id)}</b>"

    return f"\u274c Item not found: <code>{item_id}</code>"


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
        temp_url = img_result["url"]
        filename = f"blog-header-{handle}.png"
        header_image_url = upload_to_shopify(temp_url, filename)
        send_message(f"\u2705 Header image uploaded to Shopify CDN")
    except Exception as img_err:
        send_message(f"\u26a0\ufe0f Image generation skipped: {img_err}")

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
    published_url = f"https://gadgetgeekspro.myshopify.com/blogs/news/{article_handle}"

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


def _cmd_run(args: list) -> str:
    """Show instructions for manual department trigger."""
    if not args:
        return (
            "\u26a0\ufe0f Usage: /run <department>\n\n"
            "Available: intel, seo, content, email, social_morning, "
            "social_afternoon, cro, x_intel, image_prompts, prompt_qa, "
            "blog_writer, blog_qa, blog_publish, gm_report, gm_queue"
        )

    dept = args[0]
    return (
        f"\u23f3 To run <b>{dept}</b> manually:\n"
        f"Go to GitHub Actions \u2192 find the workflow \u2192 Run workflow\n\n"
        f"<i>Direct Telegram triggers coming soon.</i>"
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
