#!/usr/bin/env python3
"""
GadgetGeeks Pro — JSON to SQLite Importer
Reads all existing JSON files and populates the database.
Run once to migrate, then agents use db_helper.py going forward.

JSON files are NOT modified — they stay as archive/backup.
"""

import sqlite3
import json
import os

BASE = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE, "ggp.db")


def load_json(relative_path):
    path = os.path.join(BASE, relative_path)
    if not os.path.exists(path):
        print(f"  SKIP: {relative_path} not found")
        return None
    with open(path, "r") as f:
        return json.load(f)


def import_inventory(conn):
    """Import from config/store-inventory.json"""
    print("\n── Importing inventory ──")
    data = load_json("config/store-inventory.json")
    if not data:
        return

    products = data.get("products", {})
    count = 0
    for handle, name in products.items():
        # Categorize by handle prefix
        if "iphone" in handle:
            category = "iphone"
        elif "samsung" in handle or "galaxy" in handle:
            category = "samsung"
        elif "ipad" in handle:
            category = "ipad"
        elif "macbook" in handle:
            category = "macbook"
        elif "watch" in handle:
            category = "watch"
        elif "airpod" in handle:
            category = "airpods"
        else:
            category = "accessory"

        try:
            conn.execute(
                "INSERT OR IGNORE INTO inventory (handle, name, category) VALUES (?, ?, ?)",
                (handle, name, category)
            )
            count += 1
        except Exception as e:
            print(f"  ERROR: {handle}: {e}")

    conn.commit()
    print(f"  Imported {count} products")


def import_campaigns(conn):
    """Import from departments/social/campaigns/ and email/campaigns.json"""
    print("\n── Importing campaigns ──")

    # Grade C bundle campaign
    data = load_json("departments/social/campaigns/grade-c-bundle-test.json")
    if data:
        products = json.dumps(data.get("_products", []))
        bundle = json.dumps(data.get("_bundle_includes", []))
        angles = json.dumps([a.get("hook") for a in data.get("angles", [])])

        conn.execute(
            """INSERT OR REPLACE INTO campaigns
            (id, name, type, status, products, price_point, bundle_includes, angles, blog_correlation, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "grade-c-bundle-test",
                data.get("_campaign", "Grade C Bundle Test"),
                "social_test",
                "active",
                products,
                data.get("_price_point", ""),
                bundle,
                angles,
                data.get("_blog_correlation", ""),
                data.get("_purpose", "")
            )
        )
        print("  Imported: Grade C Bundle Test campaign")

    # iPhone 14/13 bundle campaign (from today's session)
    conn.execute(
        """INSERT OR REPLACE INTO campaigns
        (id, name, type, status, products, price_point, bundle_includes, angles, target_audience, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "iphone14-13-bundle-push",
            "iPhone 14/13 Bundle Push — $309/$270",
            "social_push",
            "active",
            json.dumps(["iPhone 14 Grade C", "iPhone 13 Grade C"]),
            "$309 (iPhone 14) / $270 (iPhone 13)",
            json.dumps(["phone", "brand new screen", "100% battery", "MagSafe case", "screen protector", "camera lens cover", "charger"]),
            json.dumps([
                "Battery transparency",
                "Bundle value stack",
                "Carrier trap math",
                "Screen replacement honesty",
                "Backup phone insurance",
                "Tucson local",
                "Blind test",
            ]),
            "Tucson AZ, 25-45, phone shoppers",
            "10 phones in stock. Colors: black, white, blue, yellow. 1000+ rebuilt. 90-day warranty."
        )
    )
    print("  Imported: iPhone 14/13 Bundle Push campaign")

    conn.commit()


def import_scripts(conn):
    """Import from departments/social/video-scripts-20260315.json"""
    print("\n── Importing scripts ──")
    data = load_json("departments/social/video-scripts-20260315.json")
    if not data:
        return

    count = 0
    for script in data:
        try:
            conn.execute(
                """INSERT OR IGNORE INTO scripts
                (id, product, price, length, hook, full_script, word_count, hook_type, angle, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    script.get("script_id", f"vid_{count}"),
                    script.get("product", ""),
                    script.get("price", 0),
                    script.get("length", "30s"),
                    script.get("hook", ""),
                    script.get("full_avatar_script", ""),
                    script.get("word_count", 0),
                    script.get("hook_type", ""),
                    script.get("body_type", ""),
                    "written"
                )
            )
            count += 1
        except Exception as e:
            print(f"  ERROR script {count}: {e}")

    # Import the 7 approved scripts from today's session
    approved_scripts = [
        {
            "id": "iphone14_battery_transparency",
            "campaign_id": "iphone14-13-bundle-push",
            "product": "iPhone 14",
            "price": 309,
            "length": "15s",
            "hook": "Most refurb sellers ship at 80% battery.",
            "full_script": "Most refurb sellers ship at 80% battery. We ship at 100%. iPhone 14, $309. Link in bio.",
            "hook_type": "contrast",
            "angle": "battery_transparency"
        },
        {
            "id": "iphone14_value_stack",
            "campaign_id": "iphone14-13-bundle-push",
            "product": "iPhone 14",
            "price": 309,
            "length": "15s",
            "hook": "iPhone 14, brand new screen, 100% battery",
            "full_script": "iPhone 14, brand new screen, 100% battery, MagSafe case, screen protector, lens cover, charger. $309 for everything you're looking at. Link in bio.",
            "hook_type": "value_stack",
            "angle": "bundle_value"
        },
        {
            "id": "iphone14_carrier_trap",
            "campaign_id": "iphone14-13-bundle-push",
            "product": "iPhone 14",
            "price": 309,
            "length": "15s",
            "hook": "Your carrier charges you $40 a month for 24 months",
            "full_script": "Your carrier charges you $40 a month for 24 months — that's $960 for one phone. This iPhone 14 is $309, unlocked, one payment plan. Link in bio.",
            "hook_type": "loss_aversion",
            "angle": "carrier_trap"
        },
        {
            "id": "iphone14_screen_honesty",
            "campaign_id": "iphone14-13-bundle-push",
            "product": "iPhone 14",
            "price": 309,
            "length": "15s",
            "hook": "We don't polish the old screen and call it good.",
            "full_script": "We don't polish the old screen and call it good. We replace it with a brand new one. iPhone 14, $309, 100% battery. Link in bio.",
            "hook_type": "honesty",
            "angle": "screen_replacement"
        },
        {
            "id": "iphone13_backup_phone",
            "campaign_id": "iphone14-13-bundle-push",
            "product": "iPhone 13",
            "price": 270,
            "length": "15s",
            "hook": "I broke my phone last month",
            "full_script": "I broke my phone last month, and even with insurance I waited three days for a replacement. Now I keep a $270 iPhone 13 in my nightstand. Two-minute SIM swap and I'm back. Link in bio.",
            "hook_type": "personal_story",
            "angle": "backup_phone"
        },
        {
            "id": "iphone14_tucson_local",
            "campaign_id": "iphone14-13-bundle-push",
            "product": "iPhone 14",
            "price": 309,
            "length": "15s",
            "hook": "Tucson —",
            "full_script": "Tucson — iPhone 14 with a brand new screen, 100% battery, full accessory kit. $309, no contract, it's yours. 10 left. Link in bio.",
            "hook_type": "geo_target",
            "angle": "local_tucson"
        },
        {
            "id": "iphone14_blind_test",
            "campaign_id": "iphone14-13-bundle-push",
            "product": "iPhone 14",
            "price": 309,
            "length": "15s",
            "hook": "One of these cost $599 from Apple.",
            "full_script": "One of these cost $599 from Apple. The other one cost $309 from me. Same speed, same camera, same screen — except mine came with a case, protector, lens cover and charger. Theirs came with a cable.",
            "hook_type": "comparison",
            "angle": "blind_test"
        }
    ]

    for s in approved_scripts:
        word_count = len(s["full_script"].split())
        conn.execute(
            """INSERT OR REPLACE INTO scripts
            (id, campaign_id, product, price, length, hook, full_script, word_count, hook_type, angle, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                s["id"], s["campaign_id"], s["product"], s["price"], s["length"],
                s["hook"], s["full_script"], word_count, s["hook_type"], s["angle"],
                "written"
            )
        )

    count += len(approved_scripts)
    conn.commit()
    print(f"  Imported {count} scripts ({len(approved_scripts)} approved + rest from JSON)")


def import_content_calendar(conn):
    """Import from departments/social/calendar.json"""
    print("\n── Importing content calendar ──")
    data = load_json("departments/social/calendar.json")
    if not data:
        return

    posts = data.get("posts", [])
    count = 0
    for post in posts:
        platforms = post.get("platforms", [])
        for platform in platforms:
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO content_calendar
                    (date, time, platform, content_type, status)
                    VALUES (?, ?, ?, ?, ?)""",
                    (
                        post.get("date", ""),
                        post.get("time", ""),
                        platform,
                        post.get("content_type", ""),
                        "posted" if post.get("date", "9999") < "2026-03-18" else "scheduled"
                    )
                )
                count += 1
            except Exception as e:
                print(f"  ERROR calendar: {e}")

    conn.commit()
    print(f"  Imported {count} calendar entries")


def import_email_campaigns(conn):
    """Import from departments/email/campaigns.json"""
    print("\n── Importing email campaigns ──")
    data = load_json("departments/email/campaigns.json")
    if not data:
        return

    campaigns = data.get("campaigns", [])
    for camp in campaigns:
        try:
            conn.execute(
                """INSERT OR REPLACE INTO email_campaigns
                (id, name, type, status, segment, theme, estimated_send_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    camp.get("id", ""),
                    camp.get("name", ""),
                    camp.get("type", ""),
                    camp.get("status", "queued"),
                    camp.get("segment", ""),
                    camp.get("theme", ""),
                    camp.get("estimated_send_count", "")
                )
            )
        except Exception as e:
            print(f"  ERROR email: {e}")

    conn.commit()
    print(f"  Imported {len(campaigns)} email campaigns")


def import_alerts(conn):
    """Import from departments/analytics/daily-report.json"""
    print("\n── Importing alerts ──")
    data = load_json("departments/analytics/daily-report.json")
    if not data:
        return

    alerts = data.get("alerts", [])
    count = 0
    for alert in alerts:
        try:
            conn.execute(
                """INSERT OR IGNORE INTO alerts
                (severity, type, message, source, recommended_action, status)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    alert.get("severity", "medium"),
                    alert.get("type", "unknown"),
                    alert.get("message", ""),
                    alert.get("page_or_query", ""),
                    alert.get("recommended_action", ""),
                    "open"
                )
            )
            count += 1
        except Exception as e:
            print(f"  ERROR alert: {e}")

    conn.commit()
    print(f"  Imported {count} alerts")


def import_performance(conn):
    """Import summary metrics from daily-report.json"""
    print("\n── Importing performance metrics ──")
    data = load_json("departments/analytics/daily-report.json")
    if not data:
        return

    report_date = data.get("report_date", "")
    summary = data.get("summary", {})
    count = 0
    for metric_name, values in summary.items():
        try:
            conn.execute(
                """INSERT OR IGNORE INTO performance
                (date, source, metric, value, previous_value, change_pct)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    report_date,
                    "google_analytics",
                    metric_name,
                    values.get("current", 0),
                    values.get("previous", 0),
                    0 if values.get("change_pct") in ("NEW_SITE", "NO_DATA") else values.get("change_pct", 0)
                )
            )
            count += 1
        except Exception as e:
            print(f"  ERROR metric: {e}")

    conn.commit()
    print(f"  Imported {count} performance metrics")


def update_iphone_bundle_inventory(conn):
    """Set actual inventory for the iPhone 14/13 bundle push."""
    print("\n── Updating iPhone bundle inventory ──")

    # iPhone 14 — $309, 10 in stock, multiple colors
    conn.execute(
        """UPDATE inventory SET
        grade = 'C', price = 309, colors = ?, stock_count = 10,
        battery_health = 100,
        bundle_includes = ?,
        status = 'active',
        updated_at = datetime('now')
        WHERE handle = 'apple-iphone-14'""",
        (
            json.dumps(["black", "white", "blue", "yellow"]),
            json.dumps(["brand new screen", "100% battery", "MagSafe case", "screen protector", "camera lens cover", "charger"])
        )
    )

    # iPhone 13 — $270
    conn.execute(
        """UPDATE inventory SET
        grade = 'C', price = 270, colors = ?,  stock_count = 10,
        battery_health = 100,
        bundle_includes = ?,
        status = 'active',
        updated_at = datetime('now')
        WHERE handle = 'apple-iphone-13'""",
        (
            json.dumps(["black", "white", "blue"]),
            json.dumps(["brand new screen", "100% battery", "MagSafe case", "screen protector", "camera lens cover", "charger"])
        )
    )

    conn.commit()
    print("  Updated iPhone 14 ($309) and iPhone 13 ($270) with bundle details")


def main():
    print("=" * 50)
    print("GadgetGeeks Pro — JSON → SQLite Import")
    print("=" * 50)

    conn = sqlite3.connect(DB_PATH)

    import_inventory(conn)
    import_campaigns(conn)
    import_scripts(conn)
    import_content_calendar(conn)
    import_email_campaigns(conn)
    import_alerts(conn)
    import_performance(conn)
    update_iphone_bundle_inventory(conn)

    # Final counts
    print("\n" + "=" * 50)
    print("IMPORT COMPLETE — Final counts:")
    for table in ["inventory", "campaigns", "scripts", "content_calendar", "email_campaigns", "performance", "alerts"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count} rows")

    conn.close()
    print(f"\nDatabase: {DB_PATH}")
    print("Agents can now use: from scripts.db_helper import db")


if __name__ == "__main__":
    main()
