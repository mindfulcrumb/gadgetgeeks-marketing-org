#!/usr/bin/env python3
"""
GadgetGeeks Pro — Google Sheets Command Center Setup
Creates the master Google Sheet and populates it with initial data.

Run this ONCE to create the sheet, then agents use sheets_helper.py going forward.

Requires:
    GOOGLE_SERVICE_ACCOUNT_KEY - JSON key (env var or file path)
    pip install google-api-python-client google-auth gspread

After creation, share the sheet with your personal Google account
so you can view it on your phone.
"""

import json
import os
import sys
from pathlib import Path

try:
    import gspread
    from google.oauth2 import service_account
except ImportError:
    print("Installing required packages...")
    os.system("pip install gspread google-api-python-client google-auth")
    import gspread
    from google.oauth2 import service_account

REPO_ROOT = Path(__file__).parent.parent
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# After creation, store the sheet ID here so all agents use the same one
SHEET_ID_FILE = REPO_ROOT / "config" / "sheets-config.json"


def get_credentials():
    """Load Google service account credentials."""
    key_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "")

    if key_json and key_json.startswith("{"):
        # JSON string in env var
        key_data = json.loads(key_json)
    elif key_json and os.path.exists(key_json):
        # File path in env var
        with open(key_json) as f:
            key_data = json.loads(f.read())
    else:
        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_KEY not set. "
            "Set it to the JSON key contents or a file path."
        )

    return service_account.Credentials.from_service_account_info(
        key_data, scopes=SCOPES
    )


def create_sheet(creds):
    """Create the master Google Sheet with all tabs."""
    gc = gspread.authorize(creds)

    # Create the spreadsheet
    sh = gc.create("GGP Command Center")
    print(f"Created sheet: {sh.url}")
    print(f"Sheet ID: {sh.id}")

    # ── Tab 1: Dashboard ──
    ws = sh.sheet1
    ws.update_title("Dashboard")
    ws.update("A1:B1", [["GadgetGeeks Pro Command Center", ""]])
    ws.update("A3:B3", [["Last Updated", ""]])
    ws.update("A5:E5", [["Metric", "Value", "Previous", "Change", "Status"]])
    ws.update("A6:E11", [
        ["Total Sessions", "", "", "", ""],
        ["Organic Sessions", "", "", "", ""],
        ["Conversions", "", "", "", ""],
        ["Revenue", "", "", "", ""],
        ["Bounce Rate", "", "", "", ""],
        ["iPhones In Stock", "", "", "", ""],
    ])
    ws.update("A13:C13", [["Active Alerts", "", ""]])
    ws.update("A14:C14", [["Severity", "Message", "Action"]])
    ws.format("A1", {"textFormat": {"bold": True, "fontSize": 16}})
    ws.format("A5:E5", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})
    ws.format("A14:C14", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})

    # ── Tab 2: Inventory ──
    inv = sh.add_worksheet(title="Inventory", rows=200, cols=12)
    inv.update("A1:L1", [[
        "Handle", "Name", "Category", "Grade", "Price",
        "Compare At", "Colors", "Stock", "Battery Health",
        "Bundle Includes", "Status", "Updated"
    ]])
    inv.format("A1:L1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})

    # ── Tab 3: Campaigns ──
    camp = sh.add_worksheet(title="Campaigns", rows=50, cols=12)
    camp.update("A1:L1", [[
        "ID", "Name", "Type", "Status", "Products",
        "Price Point", "Bundle", "Target Audience",
        "Angles", "Start Date", "End Date", "Notes"
    ]])
    camp.format("A1:L1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})

    # ── Tab 4: Scripts ──
    scripts = sh.add_worksheet(title="Scripts", rows=100, cols=16)
    scripts.update("A1:P1", [[
        "ID", "Campaign", "Product", "Price", "Length",
        "Hook", "Full Script", "Angle", "Status",
        "Filmed", "Edited", "Posted", "Platform",
        "Views", "Likes", "Comments"
    ]])
    scripts.format("A1:P1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})

    # ── Tab 5: Content Calendar ──
    cal = sh.add_worksheet(title="Content Calendar", rows=200, cols=10)
    cal.update("A1:J1", [[
        "Date", "Time", "Platform", "Content Type",
        "Script ID", "Campaign", "Caption",
        "Hashtags", "Status", "Post URL"
    ]])
    cal.format("A1:J1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})

    # ── Tab 6: Email Campaigns ──
    email = sh.add_worksheet(title="Email Campaigns", rows=50, cols=12)
    email.update("A1:L1", [[
        "ID", "Name", "Type", "Status", "Segment",
        "Theme", "Subject Line", "Preview Text",
        "Est. Send Count", "Send Date", "Open Rate", "Click Rate"
    ]])
    email.format("A1:L1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})

    # ── Tab 7: SEO Keywords ──
    seo = sh.add_worksheet(title="SEO Keywords", rows=100, cols=8)
    seo.update("A1:H1", [[
        "Keyword", "Priority", "Volume", "Current Rank",
        "Trend", "Geo", "Has Content", "Content URL"
    ]])
    seo.format("A1:H1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})

    # ── Tab 8: Performance Log ──
    perf = sh.add_worksheet(title="Performance", rows=500, cols=8)
    perf.update("A1:H1", [[
        "Date", "Source", "Metric", "Value",
        "Previous", "Change %", "Alert", "Action"
    ]])
    perf.format("A1:H1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})

    # ── Tab 9: Agent Log ──
    agent_log = sh.add_worksheet(title="Agent Log", rows=1000, cols=7)
    agent_log.update("A1:G1", [[
        "Timestamp", "Agent", "Department", "Action",
        "Status", "Details", "Tokens Used"
    ]])
    agent_log.format("A1:G1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})

    return sh


def seed_inventory(sh, repo_root):
    """Populate Inventory tab from store-inventory.json + SQLite data."""
    inv = sh.worksheet("Inventory")

    # Load from SQLite if available
    db_path = repo_root / "ggp.db"
    if db_path.exists():
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT handle, name, category, grade, price, compare_at_price, "
            "colors, stock_count, battery_health, bundle_includes, status, updated_at "
            "FROM inventory ORDER BY category, name"
        ).fetchall()
        conn.close()

        data = []
        for r in rows:
            data.append([
                r["handle"], r["name"], r["category"],
                r["grade"] or "", r["price"] or "",
                r["compare_at_price"] or "", r["colors"] or "",
                r["stock_count"] or 0, r["battery_health"] or "",
                r["bundle_includes"] or "", r["status"] or "",
                r["updated_at"] or ""
            ])

        if data:
            inv.update(f"A2:L{len(data)+1}", data)
            print(f"  Inventory: {len(data)} products")
    else:
        print("  Inventory: SQLite not found, skipping seed")


def seed_campaigns(sh, repo_root):
    """Populate Campaigns tab."""
    camp = sh.worksheet("Campaigns")
    db_path = repo_root / "ggp.db"
    if db_path.exists():
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM campaigns").fetchall()
        conn.close()

        data = []
        for r in rows:
            data.append([
                r["id"], r["name"], r["type"], r["status"],
                r["products"] or "", r["price_point"] or "",
                r["bundle_includes"] or "", r["target_audience"] or "",
                r["angles"] or "", r["start_date"] or "",
                r["end_date"] or "", r["notes"] or ""
            ])

        if data:
            camp.update(f"A2:L{len(data)+1}", data)
            print(f"  Campaigns: {len(data)} campaigns")


def seed_scripts(sh, repo_root):
    """Populate Scripts tab."""
    scripts = sh.worksheet("Scripts")
    db_path = repo_root / "ggp.db"
    if db_path.exists():
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, campaign_id, product, price, length, hook, "
            "full_script, angle, status, filmed, edited, posted, "
            "platform, views, likes, comments FROM scripts"
        ).fetchall()
        conn.close()

        data = []
        for r in rows:
            data.append([
                r["id"], r["campaign_id"] or "", r["product"],
                r["price"] or "", r["length"], r["hook"],
                r["full_script"], r["angle"] or "", r["status"],
                "Yes" if r["filmed"] else "No",
                "Yes" if r["edited"] else "No",
                "Yes" if r["posted"] else "No",
                r["platform"] or "", r["views"] or 0,
                r["likes"] or 0, r["comments"] or 0
            ])

        if data:
            scripts.update(f"A2:P{len(data)+1}", data)
            print(f"  Scripts: {len(data)} scripts")


def seed_emails(sh, repo_root):
    """Populate Email Campaigns tab."""
    email = sh.worksheet("Email Campaigns")
    db_path = repo_root / "ggp.db"
    if db_path.exists():
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM email_campaigns").fetchall()
        conn.close()

        data = []
        for r in rows:
            data.append([
                r["id"], r["name"], r["type"], r["status"],
                r["segment"] or "", r["theme"] or "",
                r["subject_line"] or "", r["preview_text"] or "",
                r["estimated_send_count"] or "", r["send_date"] or "",
                r["open_rate"] or "", r["click_rate"] or ""
            ])

        if data:
            email.update(f"A2:L{len(data)+1}", data)
            print(f"  Emails: {len(data)} campaigns")


def seed_seo(sh, repo_root):
    """Populate SEO Keywords tab."""
    seo = sh.worksheet("SEO Keywords")
    kw_path = repo_root / "departments" / "seo" / "keywords.json"
    if kw_path.exists():
        with open(kw_path) as f:
            kw_data = json.load(f)

        data = []
        for kw in kw_data.get("keywords", []):
            data.append([
                kw.get("term", ""),
                kw.get("priority", ""),
                kw.get("volume_estimate", ""),
                kw.get("current_ranking", "") or "",
                kw.get("trend", "") or "",
                kw.get("geo", "") or "national",
                "", ""
            ])

        if data:
            seo.update(f"A2:H{len(data)+1}", data)
            print(f"  SEO: {len(data)} keywords")


def seed_alerts(sh, repo_root):
    """Populate Dashboard alerts from SQLite."""
    dash = sh.worksheet("Dashboard")
    db_path = repo_root / "ggp.db"
    if db_path.exists():
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT severity, message, recommended_action FROM alerts WHERE status = 'open' "
            "ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 ELSE 3 END"
        ).fetchall()
        conn.close()

        data = [[r["severity"], r["message"], r["recommended_action"] or ""] for r in rows]
        if data:
            dash.update(f"A15:C{14+len(data)}", data)
            print(f"  Alerts: {len(data)} active")


def save_config(sheet_id, sheet_url, service_email):
    """Save sheet config so all agents know where to write."""
    config = {
        "sheet_id": sheet_id,
        "sheet_url": sheet_url,
        "service_account_email": service_email,
        "tabs": [
            "Dashboard", "Inventory", "Campaigns", "Scripts",
            "Content Calendar", "Email Campaigns", "SEO Keywords",
            "Performance", "Agent Log"
        ],
        "created": "2026-03-19",
        "notes": "Share this sheet with your personal Google account to view on phone"
    }

    SHEET_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SHEET_ID_FILE, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\nConfig saved to {SHEET_ID_FILE}")


def main():
    print("=" * 50)
    print("GGP Command Center — Google Sheet Setup")
    print("=" * 50)

    # Get credentials
    print("\n[1/4] Loading credentials...")
    creds = get_credentials()
    sa_email = creds.service_account_email
    print(f"  Service account: {sa_email}")

    # Create sheet
    print("\n[2/4] Creating Google Sheet...")
    sh = create_sheet(creds)
    print(f"  URL: {sh.url}")
    print(f"  ID: {sh.id}")

    # Seed data
    print("\n[3/4] Seeding data from SQLite...")
    seed_inventory(sh, REPO_ROOT)
    seed_campaigns(sh, REPO_ROOT)
    seed_scripts(sh, REPO_ROOT)
    seed_emails(sh, REPO_ROOT)
    seed_seo(sh, REPO_ROOT)
    seed_alerts(sh, REPO_ROOT)

    # Save config
    print("\n[4/4] Saving config...")
    save_config(sh.id, sh.url, sa_email)

    print("\n" + "=" * 50)
    print("SETUP COMPLETE")
    print(f"Sheet URL: {sh.url}")
    print(f"\nNEXT STEP: Share this sheet with your personal Gmail.")
    print(f"The service account ({sa_email}) owns it.")
    print(f"Run: sheets_helper.py share <your-email@gmail.com>")
    print("=" * 50)


if __name__ == "__main__":
    main()
