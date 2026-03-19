#!/usr/bin/env python3
"""
GadgetGeeks Pro — SQLite Command Center
Creates the central database that replaces scattered JSON reads.
Agents query specific rows instead of reading entire files.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ggp.db")


def create_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ── Table 1: inventory ──
    # Replaces store-inventory.json (200+ lines read every time)
    c.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            grade TEXT DEFAULT 'A',
            price REAL,
            compare_at_price REAL,
            colors TEXT,
            stock_count INTEGER DEFAULT 0,
            battery_health INTEGER,
            bundle_includes TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Table 2: campaigns ──
    # Replaces scattered campaign files across departments
    c.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            products TEXT,
            offer TEXT,
            price_point TEXT,
            bundle_includes TEXT,
            target_audience TEXT,
            angles TEXT,
            start_date TEXT,
            end_date TEXT,
            blog_correlation TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Table 3: scripts ──
    # Replaces video-scripts-20260315.json (7,039 lines!)
    c.execute("""
        CREATE TABLE IF NOT EXISTS scripts (
            id TEXT PRIMARY KEY,
            campaign_id TEXT,
            product TEXT,
            price REAL,
            length TEXT DEFAULT '15s',
            hook TEXT NOT NULL,
            full_script TEXT NOT NULL,
            word_count INTEGER,
            hook_type TEXT,
            angle TEXT,
            status TEXT DEFAULT 'written',
            filmed INTEGER DEFAULT 0,
            edited INTEGER DEFAULT 0,
            posted INTEGER DEFAULT 0,
            platform TEXT,
            post_date TEXT,
            post_url TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
    """)

    # ── Table 4: content_calendar ──
    # Replaces social/calendar.json
    c.execute("""
        CREATE TABLE IF NOT EXISTS content_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT,
            platform TEXT NOT NULL,
            content_type TEXT,
            script_id TEXT,
            campaign_id TEXT,
            caption TEXT,
            hashtags TEXT,
            status TEXT DEFAULT 'scheduled',
            post_url TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (script_id) REFERENCES scripts(id),
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
    """)

    # ── Table 5: email_campaigns ──
    # Replaces email/campaigns.json
    c.execute("""
        CREATE TABLE IF NOT EXISTS email_campaigns (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            status TEXT DEFAULT 'queued',
            segment TEXT,
            theme TEXT,
            subject_line TEXT,
            preview_text TEXT,
            estimated_send_count TEXT,
            send_date TEXT,
            open_rate REAL,
            click_rate REAL,
            conversions INTEGER DEFAULT 0,
            revenue REAL DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Table 6: performance ──
    # Replaces analytics/daily-report.json (read in full every time)
    c.execute("""
        CREATE TABLE IF NOT EXISTS performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            source TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL NOT NULL,
            previous_value REAL,
            change_pct REAL,
            severity TEXT,
            alert_message TEXT,
            recommended_action TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Table 7: alerts ──
    # Quick-access table for active issues
    c.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            severity TEXT NOT NULL,
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            source TEXT,
            status TEXT DEFAULT 'open',
            recommended_action TEXT,
            resolved_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Indexes for fast queries ──
    c.execute("CREATE INDEX IF NOT EXISTS idx_inventory_category ON inventory(category)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_inventory_status ON inventory(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_scripts_campaign ON scripts(campaign_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_scripts_status ON scripts(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_calendar_date ON content_calendar(date)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_calendar_platform ON content_calendar(platform)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_performance_date ON performance(date)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)")

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")
    print("Tables: inventory, campaigns, scripts, content_calendar, email_campaigns, performance, alerts")


if __name__ == "__main__":
    create_database()
