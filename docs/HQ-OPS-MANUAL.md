# GadgetGeeks Marketing HQ — Operations Manual

## Architecture Overview

```
                    +------------------+
                    |   TELEGRAM BOT   |
                    | @GGP_MA_Bot      |
                    | (every 5 min)    |
                    +--------+---------+
                             |
                    /run  /xavier  /boss
                             |
                    +--------v---------+
                    | GITHUB ACTIONS   |
                    | (cron schedules) |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
     +--------v--------+          +--------v--------+
     | run_department.py|          | telegram_bot.py |
     | (Claude API)     |          | (poll/respond)  |
     +--------+---------+          +--------+--------+
              |                             |
     +--------v--------+          +--------v--------+
     | Department       |          | Auto-publish    |
     | Output Files     |          | (blogs, emails) |
     +------------------+          +-----------------+
```

### Data Flow

1. **Cron fires** (GitHub Actions schedule) or **boss triggers** (/run, /xavier, /boss from Telegram)
2. `run_department.py` loads agent prompt + context files + boss instructions
3. Calls **Claude API** (Sonnet for departments, Opus for GM report)
4. Parses response: file updates, queue items, social posts
5. Writes updated files, appends to queue, posts to social
6. Logs to **run-history.json**, **changelog.md**, **alert-history.json**
7. Commits + pushes to GitHub
8. Sends Telegram notification

---

## Departments & Schedules (all times UTC)

| Department | Agent | Schedule | Workflow |
|-----------|-------|----------|----------|
| Market Intel | SCOUT | Mon/Thu 10:47 | intel.yml |
| X Intelligence | HAWK | Daily 07:00 | x-intel.yml |
| SEO Daily | RANK | Daily 06:23 | seo-daily.yml |
| SEO Weekly | RANK | Monday 05:17 | seo-weekly.yml |
| Content | PLANNER | Mon/Wed/Fri 07:41 | content.yml |
| Email Marketing | MAILER | Tue/Thu 08:53 | email.yml |
| Social (Morning) | VOICE | Daily 09:11 | social-morning.yml |
| Social (Afternoon) | VOICE | Daily 16:37 | social-afternoon.yml |
| CRO | OPTIMIZER | Wednesday 11:29 | cro.yml |
| Image Prompts | LENS | Mon/Wed/Fri 08:19 | image-prompts.yml |
| Prompt QA | FOCUS | Mon/Wed/Fri 08:49 | prompt-qa.yml |
| Blog Writer | SCRIBE | Mon/Wed/Fri 09:30 | blog-writer.yml |
| Blog QA | QUILL | Mon/Wed/Fri 09:00 | blog-qa.yml |
| Blog Publisher | PRESS | Mon/Wed/Fri 10:30 | blog-publish.yml |
| Dialer (Call List) | XAVIER | Weekdays 14:15 | dialer.yml |
| Dialer (Execute) | XAVIER | Weekdays 15:45 | dialer-execute.yml |
| GM Queue | GM | Daily 18:51 | gm-queue.yml |
| GM Report | GM | Friday 07:03 | gm-report.yml |
| Telegram Poll | BOT | Every 5 min | telegram-poll.yml |
| Telegram Summary | BOT | Daily 07:00 | telegram-summary.yml |

---

## Telegram Commands

| Command | What it does |
|---------|-------------|
| `/status` | Full org status — all departments, run counts, last run times |
| `/queue` | Show pending approval items |
| `/approve <id>` | Approve a queued item (auto-publishes blogs) |
| `/reject <id>` | Reject a queued item |
| `/run <dept>` | Trigger a department workflow immediately |
| `/runall` | Trigger ALL core departments at once |
| `/xavier <instruction>` | Send a direct order to Xavier (dialer AI) |
| `/boss <dept> <instruction>` | Send a direct order to any department |
| `/blog` | Blog pipeline status |
| `/prompts` | Image prompt stats |
| `/help` | Command reference |
| Free text | Saved as GM instruction, processed on next gm_queue run |

### Boss Instructions Flow
1. You send `/xavier call the B2B lead from Miami` on Telegram
2. Bot saves instruction to `state/boss-instructions.json`
3. Bot triggers the dialer workflow via GitHub Actions
4. `run_department.py` reads boss-instructions.json and injects it into the agent prompt
5. Agent executes the instruction as highest priority
6. Instruction marked as consumed after processing

---

## File Structure

```
gadgetgeeks-marketing-org/
├── agents/custom/          # Agent prompt definitions (21 agents)
│   ├── department-context.md   # Shared context all agents read
│   ├── intel-agent.md
│   ├── seo-agent.md
│   ├── content-agent.md
│   ├── blog-writer-agent.md
│   ├── blog-copy-qa-agent.md
│   ├── blog-publisher-agent.md
│   ├── dialer-agent.md
│   └── ...
├── config/                 # Configuration
│   ├── niche.json              # Store details, audience, brand voice
│   ├── copy-rules.json         # 60+ banned words/phrases (Copy Police)
│   ├── competitors-list.json   # Competitor tracking
│   ├── store-inventory.json    # Real product/collection/page handles
│   ├── vapi.json               # Dialer phone config
│   └── telegram.json           # Bot config, chat ID
├── state/                  # Runtime state
│   ├── master.json             # Department run status
│   ├── queue.json              # Approval queue (pending/approved/rejected/completed)
│   ├── run-history.json        # Full run history with token usage + changes
│   ├── boss-instructions.json  # Telegram instructions for departments
│   ├── alert-history.json      # Persistent alert/error log
│   ├── incident-log.json       # Incident tracking with root cause analysis
│   └── telegram_offset.json    # Telegram polling state
├── departments/            # Department output files
│   ├── intel/                  # competitors.json, trends.json, customer-language.json
│   ├── seo/                    # keywords.json, opportunities.json, audit-log.md
│   ├── content/                # calendar.json, blog-pipeline.json, product-copy-queue.json
│   ├── email/                  # campaigns.json, segments.json, ab-tests.json
│   ├── social/                 # calendar.json, image-prompts.json, engagement-log.md
│   ├── cro/                    # experiments.json, metrics.json, audit-log.md
│   ├── gm/                     # weekly-report.md
│   ├── dialer/                 # call-list.json
│   └── x-intel/                # daily-brief.json
│   └── */changelog.md          # Auto-generated per-department change log
├── scripts/
│   ├── run_department.py       # Core engine — loads agent, calls Claude, executes actions
│   └── actions/                # Action modules
│       ├── telegram_bot.py     # Telegram command center
│       ├── shopify_api.py      # Shopify GraphQL queries
│       ├── vapi_caller.py      # Vapi.ai phone call API
│       ├── image_gen.py        # Gemini Imagen image generation
│       ├── copy_audit.py       # 26-check copy scanner
│       ├── resend_email.py     # Resend email API
│       ├── postiz.py           # Social media posting
│       ├── x_api.py            # X/Twitter API
│       └── github_state.py     # Git commit/push helpers
├── .github/workflows/      # GitHub Actions (21 workflow files)
├── docs/
│   ├── HQ-OPS-MANUAL.md       # This file
│   └── CREDENTIALS.md         # Credentials reference
└── requirements.txt
```

---

## Logging & Monitoring

### 1. Run History (`state/run-history.json`)
Every department run is logged with:
- Timestamp, department, model used
- Input/output token counts
- Number of file updates, queue items, social posts
- List of files changed (created/modified/deleted) with sizes
- Whether boss instructions were consumed
- Error messages if the run failed
- Aggregate stats: total runs, total tokens, total errors
- Per-department stats: runs, tokens, errors, last run

### 2. Department Changelogs (`departments/*/changelog.md`)
After each run, a diff of the department's output files is appended:
- Which files were created, modified, or deleted
- File sizes
- Summary of what the agent did (first 300 chars of analysis)

### 3. Alert History (`state/alert-history.json`)
Persistent log of all alerts/errors:
- Critical: API key missing, Claude API errors
- Info: Items queued for approval
- Keeps last 200 entries

### 4. Incident Log (`state/incident-log.json`)
Major incidents with full post-mortem:
- Root cause analysis
- Fix applied
- Lesson learned
- Preventive rule (agents read this before running)

### 5. Master Status (`state/master.json`)
Quick-glance dashboard:
- Last run timestamp per department
- Current status (ok/error/idle)
- Total run count per department

### 6. GitHub Actions Logs
Full stdout/stderr for every workflow run — accessible via GitHub UI or `gh run view`.

### 7. Telegram Notifications
Real-time alerts to your phone:
- Department start/complete notifications
- Error alerts
- Queue items needing approval
- Daily summary at 07:00 UTC

---

## Approval Pipeline

```
Agent produces output
        |
        v
Queue item added to state/queue.json (status: pending)
        |
        v
Telegram notification sent: "NEW APPROVAL NEEDED"
        |
        v
You reply /approve <id> or /reject <id>
        |
   +----+----+
   |         |
approved   rejected
   |         |
   v         v
Auto-execute  Logged
(blog publish,
 email send,
 call execute)
```

### What requires approval:
- Blog publications (auto-publishes to Shopify on approve)
- Email campaigns (auto-sends via Resend on approve)
- Phone call lists (auto-dials via Vapi on approve)
- Product copy changes
- Theme modifications

---

## Dialer (Xavier) Flow

```
1. DIALER agent runs (weekdays 14:15 UTC)
   - Scans Shopify for abandoned carts ($300+)
   - Finds inactive customers (60+ days)
   - Identifies review request candidates (7-14 days post-purchase)
   - Builds call list → queues for approval

2. You approve via Telegram: /approve <call_list_id>

3. DIALER EXECUTE runs (weekdays 15:45 UTC)
   - Reads approved calls from call-list.json
   - Creates Vapi assistants if needed (4 script types)
   - Executes calls via Vapi API
   - Logs outcomes

4. Xavier (AI voice) makes the call:
   - Friendly, not pushy
   - 5 min max per call
   - Respects do-not-call immediately
   - Voicemail detection enabled
```

**Call Scripts:**
- `abandoned_cart` — "Hey, noticed you were looking at some great phones..."
- `review_request` — "Calling to check how your new phone is working out..."
- `winback` — "It's been a while, wanted to let you know about some deals..."
- `b2b_outreach` — "We supply refurbished phones to businesses at wholesale..."

**Phone:** +1 (925) 332-3098 | **Voice:** 11Labs "Burt" | **Model:** GPT-4o

---

## Blog Pipeline

```
SCRIBE (blog_writer) → QUILL (blog_qa) → PRESS (blog_publish) → Telegram approve → Shopify
  Mon/Wed/Fri 09:30     Mon/Wed/Fri 09:00    Mon/Wed/Fri 10:30
```

1. **SCRIBE** picks topic from SEO opportunities/trends, writes full blog
2. **copy_audit.py** runs 26 automated checks (banned words, AI tells, link validation)
3. **QUILL** does deep qualitative review, scores the blog
4. **PRESS** queues for approval with SEO metadata
5. **Telegram approve** triggers auto-publish:
   - Generates header image via Gemini Imagen 4
   - Uploads to Shopify CDN
   - Creates article via GraphQL `articleCreate`
   - Sends published URL to Telegram

---

## Troubleshooting

### Agents not running on schedule
1. Check `gh workflow list -R mindfulcrumb/gadgetgeeks-marketing-org --all` — all should be "active"
2. Check `gh run list -R mindfulcrumb/gadgetgeeks-marketing-org --limit 20` for recent runs
3. GitHub cron can be delayed 5-30 min. If no runs for 24h, manually trigger: `gh workflow run <file>.yml`
4. Force-trigger all: `/runall` from Telegram

### Agent run failed
1. Check `state/alert-history.json` for error details
2. Check `state/run-history.json` for the failed run entry
3. Check GitHub Actions log: `gh run view <run_id> --log`
4. Common causes: expired API key, rate limiting, context too large

### Blog publish failed
1. Check `state/incident-log.json` for known issues
2. Verify `GEMINI_API_KEY` is set (image generation)
3. Verify Shopify credentials are valid
4. Check `departments/content/blog-pipeline.json` for blog status

### Telegram commands not working
1. Bot polls every 5 min — wait for next cycle
2. Check `state/telegram_offset.json` — offset should increment
3. Verify `TELEGRAM_BOT_TOKEN` secret is set
4. Check `config/telegram.json` for correct `chat_id`
