#!/usr/bin/env python3
"""
Mission Control Generator — GadgetGeeks Marketing HQ
Reads live state files and generates status reports.

Usage:
    python3 generate_mission_control.py status    # Show live department status
    python3 generate_mission_control.py refresh   # Regenerate mission control docs
    python3 generate_mission_control.py agents    # List all agents + last run
    python3 generate_mission_control.py schedule  # Show today's schedule
"""

import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / "state"
CONFIG_DIR = BASE_DIR / "config"
AGENTS_DIR = BASE_DIR / "agents" / "custom"

# Agent registry — codename, department, model
AGENT_REGISTRY = {
    "standup":          {"codename": "CHIEF",     "role": "Morning Standup",         "model": "sonnet",  "shift": "morning"},
    "retro":            {"codename": "CHIEF",     "role": "Evening Retro",           "model": "sonnet",  "shift": "afternoon"},
    "board_meeting":    {"codename": "CHIEF",     "role": "Weekly Board Meeting",    "model": "opus",    "shift": "morning"},
    "night_ops":        {"codename": "SENTINEL",  "role": "Night Operations",        "model": "sonnet",  "shift": "night"},
    "seo":              {"codename": "PIXEL",     "role": "Daily SEO",               "model": "sonnet",  "shift": "morning"},
    "seo_weekly":       {"codename": "PIXEL",     "role": "Weekly SEO Audit",        "model": "sonnet",  "shift": "morning"},
    "content":          {"codename": "CONTENT",   "role": "Content Briefs",          "model": "sonnet",  "shift": "morning"},
    "blog_writer":      {"codename": "SCRIBE",    "role": "Blog Writer",             "model": "sonnet",  "shift": "morning"},
    "blog_qa":          {"codename": "QUILL",     "role": "Blog QA",                 "model": "sonnet",  "shift": "morning"},
    "blog_publish":     {"codename": "PRESS",     "role": "Blog Publisher",          "model": "sonnet",  "shift": "afternoon"},
    "email":            {"codename": "BEACON",    "role": "Email Marketing",         "model": "sonnet",  "shift": "morning"},
    "social_morning":   {"codename": "VIBE",      "role": "Social (Morning)",        "model": "sonnet",  "shift": "morning"},
    "social_afternoon": {"codename": "VIBE",      "role": "Social (Afternoon)",      "model": "sonnet",  "shift": "afternoon"},
    "image_prompts":    {"codename": "LENS",      "role": "Image Prompting",         "model": "sonnet",  "shift": "morning"},
    "prompt_qa":        {"codename": "FOCUS",     "role": "Prompt QA",               "model": "sonnet",  "shift": "morning"},
    "intel":            {"codename": "SCOUT",     "role": "Market Intel",            "model": "sonnet",  "shift": "morning"},
    "x_intel":          {"codename": "ECHO",      "role": "X Intelligence",          "model": "sonnet",  "shift": "morning"},
    "cro":              {"codename": "OPTIMIZER",  "role": "CRO",                    "model": "sonnet",  "shift": "morning"},
    "gm_queue":         {"codename": "GM",        "role": "Queue Processing",        "model": "sonnet",  "shift": "afternoon"},
    "gm_report":        {"codename": "GM",        "role": "Weekly Report",           "model": "opus",    "shift": "morning"},
    "canva":            {"codename": "CANVAS",    "role": "Canva Post Designer",     "model": "sonnet",  "shift": "morning"},
    "google_trends":    {"codename": "TREND",     "role": "Google Trends Scout",     "model": "sonnet",  "shift": "morning"},
    "analytics":        {"codename": "SIGNAL",    "role": "Analytics Optimizer",     "model": "sonnet",  "shift": "morning"},
    "blog_writer_pm":   {"codename": "SCRIBE",    "role": "Blog Writer (PM)",        "model": "sonnet",  "shift": "afternoon"},
}


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def time_ago(iso_str):
    """Convert ISO timestamp to human-readable time ago."""
    if not iso_str:
        return "never"
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = now - dt
        hours = diff.total_seconds() / 3600
        if hours < 1:
            return f"{int(diff.total_seconds() / 60)}m ago"
        elif hours < 24:
            return f"{int(hours)}h ago"
        else:
            return f"{int(hours / 24)}d ago"
    except (ValueError, TypeError):
        return "unknown"


def cmd_status():
    """Show live department status from master.json."""
    master = load_json(STATE_DIR / "master.json")
    depts = master.get("departments", {})

    if not depts:
        print("No department data found in state/master.json")
        return

    print("=" * 72)
    print("  MISSION CONTROL — LIVE STATUS")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 72)
    print()

    # Group by status
    active = []
    idle = []
    errors = []

    for dept, data in sorted(depts.items()):
        info = AGENT_REGISTRY.get(dept, {"codename": "?", "role": dept, "model": "?", "shift": "?"})
        entry = {
            "dept": dept,
            "codename": info["codename"],
            "role": info["role"],
            "status": data.get("status", "unknown"),
            "last_run": data.get("last_run"),
            "runs": data.get("runs_total", 0),
            "model": info["model"],
        }
        if data.get("status") == "error":
            errors.append(entry)
        elif data.get("status") == "idle" or data.get("runs_total", 0) == 0:
            idle.append(entry)
        else:
            active.append(entry)

    if errors:
        print("  RED — ERRORS")
        print("  " + "-" * 68)
        for e in errors:
            print(f"  ! {e['codename']:10} {e['role']:25} runs={e['runs']}  last={time_ago(e['last_run'])}")
        print()

    print("  GREEN — ACTIVE")
    print("  " + "-" * 68)
    for e in active:
        print(f"  + {e['codename']:10} {e['role']:25} runs={e['runs']:<4} last={time_ago(e['last_run']):>8}  [{e['model']}]")
    print()

    if idle:
        print("  GRAY — IDLE (never run)")
        print("  " + "-" * 68)
        for e in idle:
            print(f"  - {e['codename']:10} {e['role']:25} runs=0")
    print()

    # Queue status
    queue = load_json(STATE_DIR / "queue.json")
    items = queue.get("items", [])
    pending = [i for i in items if i.get("status") == "pending"]
    if pending:
        print(f"  QUEUE: {len(pending)} item(s) pending approval")
        for item in pending[:5]:
            print(f"    - [{item.get('department', '?')}] {item.get('title', item.get('type', '?'))}")
    else:
        print("  QUEUE: Empty — no pending approvals")
    print()

    # Incidents
    incidents = load_json(STATE_DIR / "incident-log.json")
    open_incidents = [i for i in incidents.get("incidents", []) if i.get("status") == "open"]
    if open_incidents:
        print(f"  INCIDENTS: {len(open_incidents)} open")
        for inc in open_incidents[:3]:
            print(f"    - {inc.get('title', '?')}")
    else:
        print("  INCIDENTS: None open")

    print()
    print("=" * 72)


def cmd_agents():
    """List all agents with their current status."""
    master = load_json(STATE_DIR / "master.json")
    depts = master.get("departments", {})

    print()
    print(f"  {'CODENAME':10} {'ROLE':25} {'MODEL':8} {'SHIFT':10} {'RUNS':5} {'LAST RUN':>10}")
    print("  " + "-" * 75)

    for dept, info in sorted(AGENT_REGISTRY.items(), key=lambda x: x[1]["shift"]):
        data = depts.get(dept, {})
        runs = data.get("runs_total", 0)
        last = time_ago(data.get("last_run"))
        print(f"  {info['codename']:10} {info['role']:25} {info['model']:8} {info['shift']:10} {runs:<5} {last:>10}")
    print()


def cmd_schedule():
    """Show today's scheduled events."""
    today = datetime.now(timezone.utc)
    day_name = today.strftime("%A")
    day_num = today.weekday()  # 0=Mon, 6=Sun

    schedule = load_json(CONFIG_DIR / "daily-schedule.json")
    timeline = schedule.get("daily_timeline", {})

    print()
    print(f"  TODAY: {day_name} {today.strftime('%Y-%m-%d')}")
    print("  " + "=" * 60)

    # Sort by time
    events = []
    for time_str, data in timeline.items():
        if time_str.startswith("_"):
            continue
        freq = data.get("frequency", "Daily")
        # Filter by day
        skip = False
        if "Mon" in freq and day_num != 0:
            skip = True
        if "Tue" in freq and "Thu" in freq and day_num not in [1, 3]:
            skip = True
        elif "Tue" in freq and "Thu" not in freq and day_num != 1:
            skip = True
        elif "Wed" in freq and day_num != 2:
            skip = True
        elif "Thu" in freq and "Tue" not in freq and day_num != 3:
            skip = True
        elif "Fri" in freq and day_num != 4:
            skip = True
        if "Weekday" in freq and day_num > 4:
            skip = True

        if not skip:
            events.append((time_str, data))

    for time_str, data in sorted(events, key=lambda x: x[0]):
        agent = data.get("agent", "?")
        event = data.get("event", "?")
        print(f"  {time_str}  {agent:15} {event}")

    print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()
    if cmd == "status":
        cmd_status()
    elif cmd == "agents":
        cmd_agents()
    elif cmd == "schedule":
        cmd_schedule()
    elif cmd == "refresh":
        print("Mission Control docs are in docs/MISSION-CONTROL.md, docs/TEAM-ROSTER.md, docs/CALENDAR.md")
        print("These are maintained manually. Run 'status' for live data from state files.")
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
