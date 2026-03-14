# MISSION CONTROL

> GadgetGeeks Marketing HQ — Command Center
> Last updated: 2026-03-14

---

## SCREENS

| Screen | File | What it shows |
|--------|------|---------------|
| **TEAM ROSTER** | [TEAM-ROSTER.md](TEAM-ROSTER.md) | Every agent, codename, model, department, responsibilities |
| **CALENDAR** | [CALENDAR.md](CALENDAR.md) | Every scheduled task, cron job, shift — full 24h timeline |
| **STATUS** | Run `/hq` or `scope-control status` | Live department status from state/master.json |

---

## QUICK STATUS

Run this to see what's happening right now:

```bash
# Live department status
cd /Users/research/gadgetgeeks-marketing-org && python3 scripts/generate_mission_control.py status

# Regenerate all mission control screens from live data
cd /Users/research/gadgetgeeks-marketing-org && python3 scripts/generate_mission_control.py refresh

# Check GitHub Actions runs
gh run list -R mindfulcrumb/gadgetgeeks-marketing-org --limit 10
```

---

## ORG AT A GLANCE

```
                          YOU (BOSS)
                             |
                    ┌────────┴────────┐
                    │                 │
               CHIEF (CoS)      SENTINEL (Night Ops)
            Morning + Board      Night Watch
                    │
        ┌───────────┼───────────┐
        │           │           │
   VP CONTENT   VP GROWTH   VP OPERATIONS
        │           │           │
   ┌────┴────┐  ┌───┴───┐  ┌───┴───┐
   │         │  │       │  │       │
 SCRIBE   LENS PIXEL  ECHO XAVIER  GM
 QUILL   FOCUS SCOUT  VIBE         │
 PRESS  CANVAS BEACON              │
 Content       OPTIMIZER      Queue + Report
```

**24 agents** | **17 departments** | **34 workflows** | **3 shifts** | **24/7 autonomous**

---

## 3-SHIFT SYSTEM

| Shift | Hours (UTC) | Lead | Philosophy |
|-------|-------------|------|------------|
| **MORNING** | 06:00 - 13:59 | CHIEF | THE BUILD — Create content, designs, campaigns |
| **AFTERNOON** | 14:00 - 19:59 | GM | THE PUSH — Sell, engage, optimize, close |
| **NIGHT** | 20:00 - 05:59 | SENTINEL | THE WATCH — Monitor, detect, prepare |

---

## MODELS IN USE

| Model | Agents | Used For |
|-------|--------|----------|
| `claude-sonnet-4-20250514` | 22 agents | All daily operations |
| `claude-opus-4-20250514` | 2 agents | GM Report (Fri) + Board Meeting (Mon) |

---

## COMMAND REFERENCE

| Command | What it does |
|---------|-------------|
| `/hq` | Open HQ — pull state, show status |
| `/hq:team` | Show Team Roster screen |
| `/hq:calendar` | Show Calendar screen |
| `/hq:status` | Show live department status |
| `gh workflow run <file>.yml -R mindfulcrumb/gadgetgeeks-marketing-org` | Trigger a workflow |
| Telegram: `/run <dept>` | Trigger department from Telegram |
| Telegram: `/status` | Live status from Telegram |
| Telegram: `/queue` | View approval queue |

---

## DATA FLOW

```
SCOUT (Intel) ──→ trends + competitors + customer language
       ↓
PIXEL (SEO) ──→ keywords + opportunities
       ↓
SCRIBE (Blog) ──→ writes from SEO brief + intel
       ↓
QUILL (QA) ──→ 25-check copy audit
       ↓
PRESS (Publish) ──→ queues for YOUR approval
       ↓
YOU approve ──→ Blog goes live on Shopify

PARALLEL FLOW:
ECHO (X Intel) ──→ daily brief
LENS (Prompts) ──→ 10 image prompts/day
       ↓
FOCUS (QA) ──→ validates prompts
       ↓
Gemini ──→ generates images
       ↓
CANVAS ──→ 10 branded Canva designs
       ↓
VIBE (Social) ──→ posts to all platforms
```
