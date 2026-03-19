#!/usr/bin/env python3
"""
GadgetGeeks Pro — Google Sheets Helper
THE standard interface for ALL agents to read/write to the Command Center.

Every agent uses this. No exceptions. No custom Sheet logic.

Usage (from any agent or action script):
    from scripts.sheets_helper import sheets

    # Read
    sheets.get_inventory()
    sheets.get_scripts(campaign="iphone14-13-bundle-push")
    sheets.get_dashboard()
    sheets.get_campaigns()

    # Write
    sheets.update_stock("apple-iphone-14", 8)
    sheets.mark_script_filmed("iphone14_carrier_trap")
    sheets.mark_script_posted("iphone14_carrier_trap", "tiktok", "https://...")
    sheets.update_metrics("iphone14_carrier_trap", views=1500, likes=89)
    sheets.log_agent_action("social_morning", "social", "Posted 3 scripts", "success")
    sheets.add_alert("high", "conversion_drop", "Zero conversions today", "Check GA4")

    # Share with your personal account
    sheets.share("your-email@gmail.com")

CLI usage:
    python scripts/sheets_helper.py share your-email@gmail.com
    python scripts/sheets_helper.py dashboard
    python scripts/sheets_helper.py inventory
    python scripts/sheets_helper.py scripts
    python scripts/sheets_helper.py log "agent_name" "department" "did something" "success"
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import gspread
    from google.oauth2 import service_account
except ImportError:
    os.system("pip install gspread google-auth")
    import gspread
    from google.oauth2 import service_account

REPO_ROOT = Path(__file__).parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "sheets-config.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


class SheetsHelper:
    """Single interface for all agents to access the GGP Command Center sheet."""

    def __init__(self):
        self._gc = None
        self._sh = None
        self._config = None

    @property
    def config(self):
        if self._config is None:
            if not CONFIG_PATH.exists():
                raise FileNotFoundError(
                    f"Sheet config not found at {CONFIG_PATH}. "
                    "Run sheets_setup.py first."
                )
            with open(CONFIG_PATH) as f:
                self._config = json.load(f)
        return self._config

    @property
    def gc(self):
        if self._gc is None:
            key_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "")
            if key_json and key_json.startswith("{"):
                key_data = json.loads(key_json)
            elif key_json and os.path.exists(key_json):
                with open(key_json) as f:
                    key_data = json.loads(f.read())
            else:
                raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY not set")
            creds = service_account.Credentials.from_service_account_info(
                key_data, scopes=SCOPES
            )
            self._gc = gspread.authorize(creds)
        return self._gc

    @property
    def sh(self):
        if self._sh is None:
            self._sh = self.gc.open_by_key(self.config["sheet_id"])
        return self._sh

    def _now(self):
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ── Share ──

    def share(self, email, role="writer"):
        """Share the sheet with a personal Google account."""
        self.sh.share(email, perm_type="user", role=role)
        print(f"Shared with {email} as {role}")
        print(f"URL: {self.config['sheet_url']}")

    # ── Dashboard ──

    def get_dashboard(self):
        """Read the Dashboard tab. Returns dict of metrics."""
        ws = self.sh.worksheet("Dashboard")
        data = ws.get_all_values()
        return data

    def update_dashboard_metrics(self, metrics):
        """
        Update Dashboard metrics.
        metrics: list of [metric_name, value, previous, change, status]
        """
        ws = self.sh.worksheet("Dashboard")
        ws.update("B3", [[self._now()]])
        if metrics:
            ws.update(f"A6:E{5+len(metrics)}", metrics)

    def update_dashboard_alerts(self, alerts):
        """
        Update Dashboard alerts.
        alerts: list of [severity, message, action]
        """
        ws = self.sh.worksheet("Dashboard")
        # Clear old alerts (rows 15-25)
        ws.batch_clear(["A15:C25"])
        if alerts:
            ws.update(f"A15:C{14+len(alerts)}", alerts)

    # ── Inventory ──

    def get_inventory(self, category=None):
        """Get inventory. Optionally filter by category."""
        ws = self.sh.worksheet("Inventory")
        records = ws.get_all_records()
        if category:
            records = [r for r in records if r.get("Category") == category]
        return records

    def update_stock(self, handle, new_count):
        """Update stock count for a product by handle."""
        ws = self.sh.worksheet("Inventory")
        cell = ws.find(handle)
        if cell:
            # Stock is column H (8)
            ws.update_cell(cell.row, 8, new_count)
            # Updated is column L (12)
            ws.update_cell(cell.row, 12, self._now())
            return True
        return False

    def add_inventory_item(self, row_data):
        """Add a new inventory row. row_data = list of 12 values matching headers."""
        ws = self.sh.worksheet("Inventory")
        ws.append_row(row_data, value_input_option="USER_ENTERED")

    # ── Campaigns ──

    def get_campaigns(self, status=None):
        """Get campaigns. Optionally filter by status."""
        ws = self.sh.worksheet("Campaigns")
        records = ws.get_all_records()
        if status:
            records = [r for r in records if r.get("Status") == status]
        return records

    def update_campaign_status(self, campaign_id, new_status):
        """Update campaign status."""
        ws = self.sh.worksheet("Campaigns")
        cell = ws.find(campaign_id)
        if cell:
            ws.update_cell(cell.row, 4, new_status)  # Status = column D
            return True
        return False

    # ── Scripts ──

    def get_scripts(self, campaign=None, status=None):
        """Get scripts. Filter by campaign and/or status."""
        ws = self.sh.worksheet("Scripts")
        records = ws.get_all_records()
        if campaign:
            records = [r for r in records if r.get("Campaign") == campaign]
        if status:
            records = [r for r in records if r.get("Status") == status]
        return records

    def mark_script_filmed(self, script_id):
        """Mark a script as filmed."""
        ws = self.sh.worksheet("Scripts")
        cell = ws.find(script_id)
        if cell:
            ws.update_cell(cell.row, 9, "filmed")   # Status
            ws.update_cell(cell.row, 10, "Yes")      # Filmed
            return True
        return False

    def mark_script_edited(self, script_id):
        """Mark a script as edited."""
        ws = self.sh.worksheet("Scripts")
        cell = ws.find(script_id)
        if cell:
            ws.update_cell(cell.row, 9, "edited")   # Status
            ws.update_cell(cell.row, 11, "Yes")      # Edited
            return True
        return False

    def mark_script_posted(self, script_id, platform, post_url=""):
        """Mark a script as posted."""
        ws = self.sh.worksheet("Scripts")
        cell = ws.find(script_id)
        if cell:
            ws.update_cell(cell.row, 9, "posted")    # Status
            ws.update_cell(cell.row, 12, "Yes")       # Posted
            ws.update_cell(cell.row, 13, platform)    # Platform
            return True
        return False

    def update_script_metrics(self, script_id, views=0, likes=0, comments=0):
        """Update engagement metrics for a posted script."""
        ws = self.sh.worksheet("Scripts")
        cell = ws.find(script_id)
        if cell:
            ws.update_cell(cell.row, 14, views)
            ws.update_cell(cell.row, 15, likes)
            ws.update_cell(cell.row, 16, comments)
            return True
        return False

    def add_script(self, row_data):
        """Add a new script row. row_data = list of 16 values matching headers."""
        ws = self.sh.worksheet("Scripts")
        ws.append_row(row_data, value_input_option="USER_ENTERED")

    # ── Content Calendar ──

    def get_calendar(self, date=None, platform=None):
        """Get calendar entries. Filter by date and/or platform."""
        ws = self.sh.worksheet("Content Calendar")
        records = ws.get_all_records()
        if date:
            records = [r for r in records if r.get("Date") == date]
        if platform:
            records = [r for r in records if r.get("Platform") == platform]
        return records

    def add_calendar_entry(self, row_data):
        """Add a calendar entry. row_data = list of 10 values matching headers."""
        ws = self.sh.worksheet("Content Calendar")
        ws.append_row(row_data, value_input_option="USER_ENTERED")

    # ── Email Campaigns ──

    def get_emails(self, status=None):
        """Get email campaigns. Filter by status."""
        ws = self.sh.worksheet("Email Campaigns")
        records = ws.get_all_records()
        if status:
            records = [r for r in records if r.get("Status") == status]
        return records

    def update_email_status(self, email_id, new_status):
        """Update email campaign status."""
        ws = self.sh.worksheet("Email Campaigns")
        cell = ws.find(email_id)
        if cell:
            ws.update_cell(cell.row, 4, new_status)
            return True
        return False

    # ── SEO ──

    def get_seo_keywords(self, priority=None):
        """Get SEO keywords. Filter by priority."""
        ws = self.sh.worksheet("SEO Keywords")
        records = ws.get_all_records()
        if priority:
            records = [r for r in records if r.get("Priority") == priority]
        return records

    # ── Performance ──

    def log_performance(self, date, source, metric, value, previous=0, change_pct=0, alert="", action=""):
        """Log a performance metric."""
        ws = self.sh.worksheet("Performance")
        ws.append_row(
            [date, source, metric, value, previous, change_pct, alert, action],
            value_input_option="USER_ENTERED"
        )

    # ── Agent Log ──

    def log_agent_action(self, agent_name, department, action, status, details="", tokens=0):
        """
        Log an agent action. EVERY agent should call this when it runs.
        This is how we track what the org is doing.
        """
        ws = self.sh.worksheet("Agent Log")
        ws.append_row(
            [self._now(), agent_name, department, action, status, details, tokens],
            value_input_option="USER_ENTERED"
        )

    # ── Alerts ──

    def add_alert(self, severity, alert_type, message, action=""):
        """Add an alert to the Dashboard."""
        ws = self.sh.worksheet("Dashboard")
        # Find next empty row in alerts section (starting row 15)
        alerts = ws.get("A15:C50")
        next_row = 15 + len(alerts) if alerts else 15
        ws.update(f"A{next_row}:C{next_row}", [[severity, message, action]])


# Singleton — all agents import this
sheets = SheetsHelper()


# ── CLI Interface ──

def cli():
    if len(sys.argv) < 2:
        print("Usage: sheets_helper.py <command> [args]")
        print("Commands: share, dashboard, inventory, scripts, campaigns, emails, log")
        return

    cmd = sys.argv[1]

    if cmd == "share":
        if len(sys.argv) < 3:
            print("Usage: sheets_helper.py share <email>")
            return
        sheets.share(sys.argv[2])

    elif cmd == "dashboard":
        data = sheets.get_dashboard()
        for row in data:
            print(" | ".join(str(c) for c in row))

    elif cmd == "inventory":
        records = sheets.get_inventory()
        for r in records:
            if r.get("Stock", 0):
                print(f"  {r['Name']}: {r['Stock']} in stock @ ${r['Price']}")

    elif cmd == "scripts":
        campaign = sys.argv[2] if len(sys.argv) > 2 else None
        records = sheets.get_scripts(campaign=campaign)
        for r in records:
            status = r.get("Status", "?")
            print(f"  [{status}] {r.get('Hook', '')[:60]}")

    elif cmd == "campaigns":
        records = sheets.get_campaigns()
        for r in records:
            print(f"  [{r['Status']}] {r['Name']}")

    elif cmd == "emails":
        records = sheets.get_emails()
        for r in records:
            print(f"  [{r['Status']}] {r['Name']}")

    elif cmd == "log":
        if len(sys.argv) < 6:
            print("Usage: sheets_helper.py log <agent> <dept> <action> <status>")
            return
        sheets.log_agent_action(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        print("Logged.")

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    cli()
