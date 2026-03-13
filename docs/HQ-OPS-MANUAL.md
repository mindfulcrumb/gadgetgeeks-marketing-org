# GadgetGeeks Marketing HQ — Enterprise Operations Manual v2.0

**Last Updated:** 2026-03-13
**Model:** Billion-dollar company operating system — 3 shifts, daily standups, weekly board meetings, escalation chains, cross-department communication protocols.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Org Chart & Hierarchy](#org-chart--hierarchy)
3. [The 3-Shift System (24/7)](#the-3-shift-system-247)
4. [Daily Cadences](#daily-cadences)
5. [Weekly Sprint Cycle](#weekly-sprint-cycle)
6. [Full Daily Timeline](#full-daily-timeline)
7. [Department Roster (24 Agents)](#department-roster-24-agents)
8. [Cross-Department Communication](#cross-department-communication)
9. [Escalation Chain](#escalation-chain)
10. [Approval Pipeline](#approval-pipeline)
11. [Telegram Commands](#telegram-commands)
12. [File Structure](#file-structure)
13. [KPI Scorecard](#kpi-scorecard)
14. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
                     ┌─────────────────────┐
                     │    CEO / BOSS        │
                     │  (Telegram Control)  │
                     └──────────┬──────────┘
                                │
                     ┌──────────▼──────────┐
                     │   CHIEF OF STAFF    │
                     │  Standups / Retros  │
                     │  Board Meetings     │
                     │  Escalation Router  │
                     └──────────┬──────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                  │
     ┌────────▼────────┐ ┌─────▼──────┐  ┌───────▼───────┐
     │  VP of Content  │ │VP of Growth│  │VP of Operations│
     └────────┬────────┘ └─────┬──────┘  └───────┬───────┘
              │                │                  │
     ┌────────┴────┐    ┌─────┴──────┐    ┌──────┴──────┐
     │ Content     │    │ SEO        │    │ Intel       │
     │ Quality     │    │ Social     │    │ Dialer      │
     │ Visual      │    │ Email      │    │ GM          │
     │             │    │ CRO        │    │ Night Ops   │
     └─────────────┘    └────────────┘    └─────────────┘
```

### Data Flow

1. **Cron fires** (GitHub Actions schedule) or **boss triggers** (`/run`, `/xavier`, `/boss` from Telegram)
2. **Agent reads daily-standup.json** — knows what other departments did and what's expected today
3. `run_department.py` loads agent prompt + context files + boss instructions
4. Calls **Claude API** (Sonnet for departments, Opus for board meetings)
5. Parses response: file updates, queue items, social posts
6. Writes updated files, appends to queue, posts to social
7. Logs to **run-history.json**, **changelog.md**, **alert-history.json**
8. Commits + pushes to GitHub
9. Sends Telegram notification

---

## Org Chart & Hierarchy

| Level | Role | Agent | Responsibility |
|-------|------|-------|---------------|
| **L0** | CEO | Boss (Human) | Final approvals, strategic direction, Telegram control |
| **L1** | Chief of Staff | CHIEF | Standups, retros, board meetings, escalation routing, alignment |
| **L2** | VP Content | Virtual | Owns Content + Quality + Visual departments |
| **L2** | VP Growth | Virtual | Owns SEO + Social + Email + CRO departments |
| **L2** | VP Operations | Virtual | Owns Intel + Dialer + GM + Night Ops |
| **L3** | Department Heads | SCOUT, PIXEL, SCRIBE, QUILL, LENS, VIBE, BEACON, OPTIMIZER, XAVIER, GM, SENTINEL | Each owns their department's KPIs |
| **L4** | Individual Agents | 24 total | Execute specific tasks within their department |

**Full org chart:** `config/org-chart.json`

---

## The 3-Shift System (24/7)

| Shift | Hours (UTC) | Name | Lead | Focus |
|-------|-------------|------|------|-------|
| **Morning** | 06:00 - 13:59 | THE BUILD | CHIEF | Create content, designs, campaigns. Production engine. |
| **Afternoon** | 14:00 - 19:59 | THE PUSH | GM | Sell and engage. Calls, social engagement, email, CRO. |
| **Night** | 20:00 - 05:59 | THE WATCH | SENTINEL | Monitor and prepare. Health checks, incident detection, morning prep. |

### Shift Handoff Protocol

Every shift writes to `state/shift-handoff.json` before ending:
- What was completed
- What's in progress
- Blockers
- Pending approvals
- API health status
- Urgent items for next shift

**Rule:** Never start a shift without reading the previous shift's handoff.

---

## Daily Cadences

### 5 Daily Touchpoints

| Time (UTC) | Event | Owner | Purpose |
|------------|-------|-------|---------|
| **05:00** | Night prep | SENTINEL | Collect overnight metrics, prepare standup data |
| **05:30** | Night-to-Morning handoff | SENTINEL | Write handoff for CHIEF |
| **06:00** | **Morning Standup** | CHIEF | All-department status, priorities, blockers, cross-dept handoffs |
| **20:00** | **Evening Retro** | CHIEF | Day summary, what shipped/failed, night handoff |
| **00:00, 03:00** | Night health checks | SENTINEL | API health, workflow failures, stale queue detection |

### What the Standup Contains

For EACH department:
1. **What was accomplished** since last standup
2. **What's planned** for today
3. **Blockers** or dependencies needed from other departments

Plus:
- **Escalations** — items that need boss attention TODAY
- **Top 3 priorities** across the entire org
- **Cross-department handoffs** — who needs what from whom

**Output:** `state/daily-standup.json` + Telegram summary to boss

---

## Weekly Sprint Cycle

| Day | Theme | Special Events |
|-----|-------|---------------|
| **Monday** | PLAN & LAUNCH | Weekly Board Meeting (06:30), SEO deep audit (05:17), Intel run |
| **Tuesday** | CREATE & BUILD | Email campaign, heads-down production |
| **Wednesday** | OPTIMIZE & TEST | CRO audit (11:29), mid-week sprint check |
| **Thursday** | ENGAGE & SELL | Email campaign #2, Intel run #2, outbound focus |
| **Friday** | REVIEW & SHIP | GM Weekly Report (07:03), sprint retro, ship everything ready |
| **Saturday** | AUTOPILOT | Content & social only, no outbound |
| **Sunday** | MONITORING | Health monitoring, prep Monday board |

### Weekly Board Meeting (Monday 06:30 UTC)

Strategic review compiled by CHIEF:
- **KPI Scorecard** — actual vs targets with trend arrows
- **Top 3 wins** for the week
- **Misses** and why
- **Incidents** and lessons
- **Competitive landscape** changes
- **Resource efficiency** (token spend, API costs)
- **This week's top 5 priorities**
- **Decisions needed from boss**

**Output:** `departments/gm/weekly-board-minutes.md` + Telegram executive summary

**Full cadence config:** `config/weekly-cadence.json`

---

## Full Daily Timeline

All times UTC. **Bold** = governance events (new in v2.0).

| Time | Event | Agent | Shift |
|------|-------|-------|-------|
| **00:00** | **SENTINEL: Midnight health check** | SENTINEL | Night |
| **03:00** | **SENTINEL: Pre-dawn health check** | SENTINEL | Night |
| **05:00** | **SENTINEL: Morning prep** | SENTINEL | Night |
| 05:17 | PIXEL: Weekly SEO audit (Mon only) | PIXEL | Night |
| **05:30** | **SENTINEL: Night-to-morning handoff** | SENTINEL | Night→Morning |
| **06:00** | **CHIEF: Morning Standup** | CHIEF | Morning |
| 06:23 | PIXEL: Daily SEO scan | PIXEL | Morning |
| **06:30** | **CHIEF: Weekly Board Meeting (Mon only)** | CHIEF | Morning |
| 07:00 | ECHO: X Intelligence + Telegram Summary | ECHO + BOT | Morning |
| 07:41 | Content: Daily brief generation | Content Agent | Morning |
| 08:19 | LENS: Generate 10 image prompts | LENS | Morning |
| 08:49 | FOCUS: QA all 10 prompts | FOCUS | Morning |
| 08:53 | BEACON: Email campaign (Tue/Thu) | BEACON | Morning |
| 08:55 | Gemini: Generate images | Image Gen | Morning |
| 09:25 | CANVAS: Design 10 Canva posts | CANVAS | Morning |
| 09:30 | SCRIBE: Write daily blog | SCRIBE | Morning |
| 09:45 | VIBE: Morning social posts | VIBE | Morning |
| 10:00 | QUILL: Blog QA + copy audit | QUILL | Morning |
| 10:30 | PRESS: Blog publisher | PRESS | Morning |
| 10:47 | SCOUT: Market intel (Mon/Thu) | SCOUT | Morning |
| 11:29 | OPTIMIZER: CRO audit (Wed) | OPTIMIZER | Morning |
| 14:15 | XAVIER: Build call list (weekdays) | DIALER | Afternoon |
| 15:45 | XAVIER: Execute calls (weekdays) | DIALER Execute | Afternoon |
| 16:37 | VIBE: Afternoon engagement | VIBE (PM) | Afternoon |
| 18:51 | GM: Daily queue processing | GM Queue | Afternoon |
| **20:00** | **CHIEF: Evening Retro + Night Handoff** | CHIEF | Afternoon→Night |
| */5 min | Telegram: Poll for commands | BOT | All shifts |

---

## Department Roster (24 Agents)

### Content & Copy (6 agents)
| Agent | Codename | Function |
|-------|----------|----------|
| Blog Writer | SCRIBE | Writes 1 blog/day from SEO briefs |
| Blog QA | QUILL | 25-check anti-AI scanner + deep review |
| Blog Publisher | PRESS | Packages for approval, publishes on approve |
| Content Agent | — | Product descriptions, misc copy |
| Copy QA | — | Master copy auditor for all departments |
| Shopify E-Commerce | — | Catalog optimization (never auto-edits live store) |

### Visual & Design (3 agents)
| Agent | Codename | Function |
|-------|----------|----------|
| Image Prompting | LENS | 10 photorealistic prompts/day |
| Prompt QA | FOCUS | 17-check quality audit on prompts |
| Canva Designer | CANVAS | 10 branded designs/day from images |

### Growth (4 agents)
| Agent | Codename | Function |
|-------|----------|----------|
| SEO Daily | PIXEL | Daily keyword opportunity + recommendation |
| SEO Weekly | PIXEL | Monday deep audit + content gap analysis |
| Social Morning | VIBE | Create & post social content |
| Social Afternoon | VIBE | Monitor engagement, flag wins |

### Revenue (2 agents)
| Agent | Codename | Function |
|-------|----------|----------|
| Email Marketing | BEACON | 2 campaigns/week with A/B testing |
| CRO | OPTIMIZER | Conversion audits, experiment proposals |

### Intelligence (2 agents)
| Agent | Codename | Function |
|-------|----------|----------|
| Market Intel | SCOUT | Competitor analysis, trend identification |
| X Intelligence | ECHO | Real-time Twitter/X monitoring |

### Operations (2 agents)
| Agent | Codename | Function |
|-------|----------|----------|
| Dialer (List) | XAVIER | Build call lists from Shopify data |
| Dialer (Execute) | XAVIER | Execute approved calls via Vapi.ai |

### General Management (2 agents)
| Agent | Codename | Function |
|-------|----------|----------|
| GM Queue | GM | Daily queue processing |
| GM Report | GM | Friday weekly report |

### Governance (2 agents — NEW in v2.0)
| Agent | Codename | Function |
|-------|----------|----------|
| Chief of Staff | CHIEF | Standups, retros, board meetings, alignment |
| Night Operations | SENTINEL | Overnight monitoring, health checks, morning prep |

---

## Cross-Department Communication

### How Departments Talk to Each Other

Departments don't talk directly. Instead:

1. **CHIEF compiles the standup** at 06:00 UTC every morning
2. **Every agent reads `state/daily-standup.json`** before their run
3. This means SCRIBE knows what PIXEL found, VIBE knows what CANVAS designed, BEACON knows what SCOUT discovered

### Dependency Map

```
SCOUT + ECHO ──→ ALL departments (intel feeds)
       │
       ├──→ PIXEL (SEO opportunities from trends)
       │         │
       │         └──→ Content Agent (briefs from SEO)
       │                    │
       │                    └──→ SCRIBE (writes from briefs)
       │                              │
       │                              └──→ QUILL (QA review)
       │                                        │
       │                                        └──→ PRESS (publish)
       │
       ├──→ LENS (trending topics for image prompts)
       │         │
       │         └──→ FOCUS (QA prompts)
       │                    │
       │                    └──→ Gemini (generate images)
       │                              │
       │                              └──→ CANVAS (design posts)
       │                                        │
       │                                        └──→ VIBE (post to social)
       │
       ├──→ BEACON (customer language for emails)
       │
       └──→ OPTIMIZER (market context for CRO)
```

**Rule:** If a downstream department can't work because upstream didn't deliver, CHIEF flags it as a blocker in the standup.

---

## Escalation Chain

| Level | Handler | Time Limit | Examples |
|-------|---------|-----------|----------|
| **0** | Agent (auto-resolve) | Immediate | Retryable API errors, safe defaults |
| **1** | Department head | Next run (<4h) | NEEDS_WORK copy rating, failed prompt QA |
| **2** | CHIEF | Next standup/retro (<12h) | Cross-dept breaks, repeated failures, idle departments |
| **3** | Boss (Telegram) | Async | Money-spending actions, store down, expired credentials |

**Rules:**
- No incident open >48h without boss notification
- No queue item pending >24h without CHIEF flagging it
- Every escalation includes: what happened, what's blocked, recommended action

---

## Approval Pipeline

```
Agent produces output
        │
        ▼
Queue item added to state/queue.json (status: pending)
        │
        ▼
Telegram notification: "NEW APPROVAL NEEDED"
        │
        ▼
Boss replies /approve <id> or /reject <id>
        │
   ┌────┴────┐
   │         │
approved   rejected
   │         │
   ▼         ▼
Auto-execute  Logged
(blog, email,
 call, SEO)
```

**10 approval types** with specific action handlers. See `config/operations-rulebook.json` Rule 2.

---

## Telegram Commands

| Command | What it does |
|---------|-------------|
| `/status` | Full org status — all departments, run counts, last run times |
| `/queue` | Show pending approval items |
| `/approve <id>` | Approve a queued item (triggers action) |
| `/reject <id>` | Reject a queued item |
| `/run <dept>` | Trigger a department workflow |
| `/runall` | Trigger ALL core departments |
| `/xavier <instruction>` | Direct order to Xavier (dialer AI) |
| `/boss <dept> <instruction>` | Direct order to any department |
| `/blog` | Blog pipeline status |
| `/prompts` | Image prompt stats |
| `/fix_image <handle>` | Fix missing blog header image |
| `/help` | Command reference |
| Free text | Saved as GM instruction for next queue run |

---

## File Structure

```
gadgetgeeks-marketing-org/
├── agents/custom/              # 24 agent prompt definitions
│   ├── department-context.md       # Shared context (all agents read)
│   ├── chief-of-staff-agent.md     # CHIEF (standups, retros, board)
│   ├── night-ops-agent.md          # SENTINEL (overnight monitoring)
│   └── [20 department agents]
├── config/
│   ├── org-chart.json              # Hierarchy, escalation chains
│   ├── daily-schedule.json         # 24/7 schedule with 3 shifts
│   ├── weekly-cadence.json         # Sprint cycle, board meetings, KPIs
│   ├── operations-rulebook.json    # 20 rules (v2.0)
│   └── [store config, copy rules, competitors, etc.]
├── state/
│   ├── master.json                 # Department run status (v2.0)
│   ├── daily-standup.json          # Morning standup (CHIEF)
│   ├── daily-retro.json            # Evening retro (CHIEF)
│   ├── shift-handoff.json          # Shift transition notes
│   ├── night-report.json           # SENTINEL health checks
│   ├── queue.json                  # Approval queue
│   ├── run-history.json            # Run history + token usage
│   ├── incident-log.json           # Post-mortems
│   └── [boss instructions, alerts, telegram state]
├── departments/                    # Department outputs
│   └── gm/weekly-board-minutes.md  # Board meeting minutes
├── .github/workflows/              # 26 workflows
│   ├── morning-standup.yml         # Daily 06:00 UTC
│   ├── evening-retro.yml           # Daily 20:00 UTC
│   ├── night-ops.yml               # 00:00, 03:00, 05:00 UTC
│   ├── weekly-board.yml            # Monday 06:30 UTC
│   └── [22 existing workflows]
└── scripts/
    ├── run_department.py           # Core engine (4 new departments)
    └── actions/                    # Action modules
```

---

## KPI Scorecard

Tracked weekly in the Monday board meeting. Targets in `config/weekly-cadence.json`.

| Category | KPI | Target |
|----------|-----|--------|
| **Content** | Blogs published/week | 5 |
| | Blogs blocked | 0 |
| | Copy quality average | EXCELLENT |
| **SEO** | New keyword rankings/week | 3 |
| | SEO recommendations applied | 5 |
| | Organic traffic growth | 10% MoM |
| **Social** | Posts published/week | 70 (10/day) |
| | Engagement rate | >2% |
| | Follower growth/week | >50 |
| **Email** | Campaigns/week | 2 |
| | Open rate | >25% |
| | Click rate | >3% |
| | Revenue attributed | >$500/week |
| **Dialer** | Calls/week | 10 |
| | Cart recovery rate | >15% |
| **Operations** | Queue same-day processing | 100% |
| | Open incidents >48h | 0 |
| | Dead-end approvals | 0 |
| | Store uptime | 100% |
| **Visual** | Images generated/week | 50 |
| | Canva designs/week | 50 |
| | Prompt QA pass rate | >90% |

---

## Troubleshooting

### Agents not running on schedule
1. Check `gh workflow list -R mindfulcrumb/gadgetgeeks-marketing-org --all`
2. Check `gh run list -R mindfulcrumb/gadgetgeeks-marketing-org --limit 20`
3. GitHub cron can delay 5-30 min. If no runs for 24h, manually trigger
4. SENTINEL will flag missed runs at 00:00/03:00/05:00 checks

### Standup/retro not compiling
1. Check CHIEF workflow ran: `gh run list --workflow morning-standup.yml`
2. Read `state/daily-standup.json` — is the date current?
3. Manually trigger: `gh workflow run morning-standup.yml`

### Night shift missing handoff
1. Check SENTINEL ran: `gh run list --workflow night-ops.yml`
2. Read `state/shift-handoff.json` — is it stale?
3. Manually trigger: `gh workflow run night-ops.yml`

### Cross-department break (downstream blocked)
1. Check `state/daily-standup.json` — is the blocker documented?
2. Trigger the upstream department: `gh workflow run <upstream>.yml`
3. Re-trigger the blocked department after upstream completes

### Escalation needed
1. Check `config/org-chart.json` escalation chain
2. Level 0-1: auto-resolve or department head
3. Level 2: CHIEF handles at next standup/retro
4. Level 3: Telegram alert to boss with URGENT tag
