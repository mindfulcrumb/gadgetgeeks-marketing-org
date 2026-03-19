#!/usr/bin/env python3
"""
GadgetGeeks Pro — Database Helper
Token-efficient query interface for all agents.

Instead of reading a 7,000-line JSON file (~15,000 tokens),
agents call these functions and get back ~50-200 tokens.

Usage:
    from scripts.db_helper import db

    # Get campaign status
    db.campaign_status("iphone14-bundle")

    # Get all scripts for a campaign
    db.scripts_for_campaign("iphone14-bundle")

    # Check inventory
    db.stock_check("apple-iphone-14")

    # Raw query for anything else
    db.query("SELECT name, status FROM scripts WHERE filmed = 0")
"""

import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ggp.db")


class GGPDatabase:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── Raw query (for agents that need custom data) ──

    def query(self, sql, params=None):
        """Run any SELECT query. Returns list of dicts."""
        conn = self._conn()
        cursor = conn.execute(sql, params or [])
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def execute(self, sql, params=None):
        """Run INSERT/UPDATE/DELETE. Returns rowcount."""
        conn = self._conn()
        cursor = conn.execute(sql, params or [])
        conn.commit()
        rowcount = cursor.rowcount
        conn.close()
        return rowcount

    # ── Inventory ──

    def stock_check(self, handle=None, category=None):
        """Check stock for a product or category."""
        if handle:
            return self.query(
                "SELECT name, grade, price, colors, stock_count, battery_health, status FROM inventory WHERE handle = ?",
                [handle]
            )
        if category:
            return self.query(
                "SELECT handle, name, grade, price, stock_count, status FROM inventory WHERE category = ? AND stock_count > 0",
                [category]
            )
        return self.query(
            "SELECT handle, name, category, stock_count, status FROM inventory WHERE stock_count > 0 ORDER BY category, name"
        )

    def update_stock(self, handle, count):
        """Update stock count for a product."""
        return self.execute(
            "UPDATE inventory SET stock_count = ?, updated_at = datetime('now') WHERE handle = ?",
            [count, handle]
        )

    def low_stock(self, threshold=5):
        """Get products with stock below threshold."""
        return self.query(
            "SELECT handle, name, stock_count, price FROM inventory WHERE stock_count > 0 AND stock_count <= ? ORDER BY stock_count",
            [threshold]
        )

    # ── Campaigns ──

    def campaign_status(self, campaign_id=None):
        """Get campaign status. None = all active campaigns."""
        if campaign_id:
            return self.query(
                "SELECT * FROM campaigns WHERE id = ?",
                [campaign_id]
            )
        return self.query(
            "SELECT id, name, type, status, price_point, start_date FROM campaigns WHERE status != 'completed' ORDER BY start_date"
        )

    def update_campaign_status(self, campaign_id, status):
        """Update campaign status."""
        return self.execute(
            "UPDATE campaigns SET status = ?, updated_at = datetime('now') WHERE id = ?",
            [status, campaign_id]
        )

    # ── Scripts ──

    def scripts_for_campaign(self, campaign_id):
        """Get all scripts for a campaign with their status."""
        return self.query(
            "SELECT id, hook, length, status, filmed, edited, posted, platform, views, likes, comments FROM scripts WHERE campaign_id = ?",
            [campaign_id]
        )

    def unfilmed_scripts(self):
        """Get scripts that haven't been filmed yet."""
        return self.query(
            "SELECT id, campaign_id, hook, product, price FROM scripts WHERE filmed = 0 ORDER BY created_at"
        )

    def mark_filmed(self, script_id):
        """Mark a script as filmed."""
        return self.execute(
            "UPDATE scripts SET filmed = 1, status = 'filmed', updated_at = datetime('now') WHERE id = ?",
            [script_id]
        )

    def mark_posted(self, script_id, platform, post_url=None):
        """Mark a script as posted."""
        return self.execute(
            "UPDATE scripts SET posted = 1, status = 'posted', platform = ?, post_url = ?, post_date = date('now'), updated_at = datetime('now') WHERE id = ?",
            [platform, post_url, script_id]
        )

    def update_script_metrics(self, script_id, views=0, likes=0, comments=0, shares=0, clicks=0):
        """Update engagement metrics for a posted script."""
        return self.execute(
            "UPDATE scripts SET views = ?, likes = ?, comments = ?, shares = ?, clicks = ?, updated_at = datetime('now') WHERE id = ?",
            [views, likes, comments, shares, clicks, script_id]
        )

    def top_performers(self, limit=5):
        """Get top performing posted scripts by views."""
        return self.query(
            "SELECT id, hook, platform, views, likes, comments, shares, clicks FROM scripts WHERE posted = 1 ORDER BY views DESC LIMIT ?",
            [limit]
        )

    # ── Content Calendar ──

    def upcoming_posts(self, days=7):
        """Get posts scheduled in the next N days."""
        return self.query(
            "SELECT c.date, c.platform, c.content_type, c.status, s.hook FROM content_calendar c LEFT JOIN scripts s ON c.script_id = s.id WHERE c.date >= date('now') AND c.date <= date('now', '+' || ? || ' days') ORDER BY c.date, c.time",
            [days]
        )

    def posts_today(self):
        """Get today's scheduled posts."""
        return self.query(
            "SELECT c.platform, c.content_type, c.status, c.time, s.hook FROM content_calendar c LEFT JOIN scripts s ON c.script_id = s.id WHERE c.date = date('now') ORDER BY c.time"
        )

    # ── Email Campaigns ──

    def email_status(self):
        """Get all email campaign statuses."""
        return self.query(
            "SELECT id, name, type, status, segment, estimated_send_count, send_date FROM email_campaigns ORDER BY created_at"
        )

    # ── Performance & Alerts ──

    def active_alerts(self):
        """Get all open alerts."""
        return self.query(
            "SELECT severity, type, message, recommended_action FROM alerts WHERE status = 'open' ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END"
        )

    def daily_metrics(self, date=None):
        """Get performance metrics for a date. None = today."""
        if date:
            return self.query(
                "SELECT source, metric, value, previous_value, change_pct FROM performance WHERE date = ?",
                [date]
            )
        return self.query(
            "SELECT source, metric, value, previous_value, change_pct FROM performance WHERE date = (SELECT MAX(date) FROM performance)"
        )

    # ── Dashboard (the big one — replaces reading 5+ JSON files) ──

    def dashboard(self):
        """
        Full status in one call. This is what the Telegram bot uses.
        Returns everything an agent or human needs in ~200 tokens
        instead of reading 10,000+ lines of JSON (~25,000 tokens).
        """
        conn = self._conn()

        # Active campaigns
        campaigns = [dict(r) for r in conn.execute(
            "SELECT id, name, status FROM campaigns WHERE status != 'completed'"
        ).fetchall()]

        # Script pipeline
        script_stats = dict(conn.execute(
            "SELECT COUNT(*) as total, SUM(filmed) as filmed, SUM(edited) as edited, SUM(posted) as posted FROM scripts"
        ).fetchone())

        # Inventory summary
        inventory = [dict(r) for r in conn.execute(
            "SELECT category, SUM(stock_count) as total_stock FROM inventory WHERE stock_count > 0 GROUP BY category"
        ).fetchall()]

        # Low stock alerts
        low = [dict(r) for r in conn.execute(
            "SELECT name, stock_count FROM inventory WHERE stock_count > 0 AND stock_count <= 5"
        ).fetchall()]

        # Email pipeline
        emails = [dict(r) for r in conn.execute(
            "SELECT name, status FROM email_campaigns WHERE status != 'sent'"
        ).fetchall()]

        # Open alerts
        alerts = [dict(r) for r in conn.execute(
            "SELECT severity, message FROM alerts WHERE status = 'open' ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 ELSE 3 END LIMIT 5"
        ).fetchall()]

        conn.close()

        return {
            "campaigns": campaigns,
            "scripts": script_stats,
            "inventory": inventory,
            "low_stock": low,
            "emails": emails,
            "alerts": alerts
        }


# Singleton instance — agents just import db
db = GGPDatabase()


if __name__ == "__main__":
    # Quick test
    print(json.dumps(db.dashboard(), indent=2, default=str))
