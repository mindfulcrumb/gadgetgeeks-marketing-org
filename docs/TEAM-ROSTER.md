# TEAM ROSTER

> Every agent in the GadgetGeeks Marketing Org
> 24 agents | 17 departments | 3 shifts

---

## GOVERNANCE LAYER

| # | Codename | Role | Department | Model | Schedule | Responsibilities |
|---|----------|------|-----------|-------|----------|-----------------|
| 1 | **CHIEF** | Chief of Staff | Executive | Sonnet | Daily 06:00 + 20:00, Mon 06:30 | Morning standups, evening retros, Monday board meetings. Reads ALL department states. Compiles org-wide view. Sends Telegram briefings to boss. |
| 2 | **SENTINEL** | Night Operations | Operations | Sonnet | 00:00, 03:00, 05:00, 05:30 UTC | Overnight health monitoring. 3 nightly checks: store uptime, API health, workflow failures. Pre-dawn data collection. Morning handoff notes. Escalates incidents. |

---

## CONTENT & COPY

| # | Codename | Role | Department | Model | Schedule | Responsibilities |
|---|----------|------|-----------|-------|----------|-----------------|
| 3 | **SCRIBE** | Blog Writer | Content Creation | Sonnet | Daily 12:00 | Writes 1 blog/day (1,200-2,000 words). Reads standup + SEO brief + intel trends. Picks next `brief_ready` topic from pipeline. |
| 4 | **QUILL** | Blog QA | Content Quality | Sonnet | Daily 13:00 | 25-check anti-AI copy audit on every draft. Checks: banned words, triple patterns, sentence variance, specificity, human signals. Rates: EXCELLENT / GOOD / NEEDS WORK. |
| 5 | **PRESS** | Blog Publisher | Content Creation | Sonnet | Daily 14:30 | Packages `qa_approved` blogs for boss approval. Handles Shopify blog API publishing after approval. |
| 6 | — | Content Agent | Content Creation | Sonnet | Daily 07:41 | Generates daily content briefs from SEO opportunities + intel signals. Product descriptions, content calendar. |
| 7 | — | Copy QA Agent | Content Quality | Sonnet | On-demand | Master copy auditor. Deep qualitative review beyond automated checks. Reviews product copy, emails, ads. |
| 8 | — | Shopify E-Commerce | Content Creation | Sonnet | On-demand | Catalog optimization. Product descriptions, collection copy, metafield management. |

---

## VISUAL & DESIGN

| # | Codename | Role | Department | Model | Schedule | Responsibilities |
|---|----------|------|-----------|-------|----------|-----------------|
| 9 | **LENS** | Image Prompting | Visual Design | Sonnet | Daily 08:19 | Writes 10 photorealistic AI image prompts per day. Product shots, lifestyle scenes, brand imagery. |
| 10 | **FOCUS** | Prompt QA | Visual Design | Sonnet | Daily 08:49 | 17-check quality audit on all prompts from LENS. Validates: composition, lighting, brand consistency, technical specs. |
| 11 | **CANVAS** | Canva Designer | Visual Design | Sonnet | Daily 09:25 | Creates 10 branded social media designs per day from generated images. Brand-consistent templates. |
| 12 | — | Image Generator | Visual Design | Gemini Imagen 4 | Daily 08:55 | Generates actual images from FOCUS-approved prompts. Uploads to Shopify CDN. |

---

## GROWTH & MARKETING

| # | Codename | Role | Department | Model | Schedule | Responsibilities |
|---|----------|------|-----------|-------|----------|-----------------|
| 13 | **PIXEL** | SEO (Daily) | SEO | Sonnet | Daily 06:23 | Daily keyword opportunity scan. Writes today's SEO recommendation. Feeds briefs to Content + Blog. |
| 14 | **PIXEL** | SEO (Weekly) | SEO | Sonnet | Mon 05:17 | Deep weekly audit: content gap analysis, competitor SERP tracking, keyword cluster strategy. |
| 15 | **VIBE** | Social (Morning) | Social Media | Sonnet | Daily 09:45 | Creates and posts 1-2 daily social posts. Picks up CANVAS designs, writes copy, posts via Postiz. |
| 16 | **VIBE** | Social (Afternoon) | Social Media | Sonnet | Daily 16:37 | Monitors post engagement, tracks performance metrics, flags standout content, logs engagement data. |
| 17 | **SCOUT** | Market Intel | Intelligence | Sonnet | Mon/Thu 10:47 | Deep competitor analysis: pricing, features, positioning. Trend identification. Customer language mining from reviews. |
| 18 | **ECHO** | X Intelligence | Intelligence | Sonnet | Daily 07:00 | Real-time Twitter/X monitoring. Market signals, competitor mentions, trending topics, sentiment analysis. |

---

## REVENUE

| # | Codename | Role | Department | Model | Schedule | Responsibilities |
|---|----------|------|-----------|-------|----------|-----------------|
| 19 | **BEACON** | Email Marketing | Email | Sonnet | Tue/Thu 08:53 | Designs email campaigns 2x/week. Segment targeting, A/B test proposals, subject line optimization. Queues for approval. |
| 20 | **OPTIMIZER** | CRO | CRO | Sonnet | Wed 11:29 | Weekly conversion rate analysis. A/B test reviews, experiment proposals, product page recommendations. |

---

## OPERATIONS

| # | Codename | Role | Department | Model | Schedule | Responsibilities |
|---|----------|------|-----------|-------|----------|-----------------|
| 21 | **XAVIER** | Dialer (List Builder) | Dialer | Sonnet | Weekdays 14:15 | Scans Shopify for abandoned carts, win-back candidates, review requests. Builds call list for approval. |
| 22 | **XAVIER** | Dialer (Executor) | Dialer | Sonnet | Weekdays 15:45 | Executes approved calls via Vapi.ai. 4 scripts: abandoned cart, review request, winback, B2B outreach. Phone: +1 (925) 332-3098 |

---

## GENERAL MANAGEMENT

| # | Codename | Role | Department | Model | Schedule | Responsibilities |
|---|----------|------|-----------|-------|----------|-----------------|
| 23 | — | GM Queue | General Management | Sonnet | Daily 18:51 | Processes approval queue. Flags overdue items. Moves approved items to execution. End-of-day wrap. |
| 24 | — | GM Report | General Management | **Opus** | Fri 07:03 | Weekly org-wide performance report. KPI analysis, budget tracking, strategic recommendations. Heavy analysis = Opus model. |

---

## SYSTEM AGENTS (Non-Claude)

| Agent | Technology | Schedule | Purpose |
|-------|-----------|----------|---------|
| Telegram Bot | Python (telegram-poll.yml) | Every 5 min | Boss command interface. Polls for /run, /status, /queue, /boss commands. |
| Image Generator | Gemini Imagen 4 | Daily 08:55 | Generates images from approved prompts. |
| Blog Status Reporter | System script | Daily 15:00 | Sends Telegram summary of blog pipeline status. |

---

## AGENT PROMPT FILES

All agent definitions live in `/Users/research/gadgetgeeks-marketing-org/agents/custom/`:

```
chief-of-staff-agent.md     ← CHIEF
night-ops-agent.md          ← SENTINEL
blog-writer-agent.md        ← SCRIBE
blog-qa-agent.md            ← QUILL
blog-publisher-agent.md     ← PRESS
content-agent.md            ← Content
copy-qa-agent.md            ← Copy QA
shopify-ecommerce-agent.md  ← E-Commerce
image-prompting-agent.md    ← LENS
prompt-qa-agent.md          ← FOCUS
canva-post-agent.md         ← CANVAS
seo-agent.md                ← PIXEL (daily)
seo-weekly-agent.md         ← PIXEL (weekly)
social-morning-agent.md     ← VIBE (AM)
social-afternoon-agent.md   ← VIBE (PM)
intel-agent.md              ← SCOUT
x-intel-agent.md            ← ECHO
email-marketing-agent.md    ← BEACON
cro-agent.md                ← OPTIMIZER
dialer-agent.md             ← XAVIER (list)
dialer-execute-agent.md     ← XAVIER (calls)
gm-queue-agent.md           ← GM Queue
gm-report-agent.md          ← GM Report
```

---

## HOW TO ADD A NEW AGENT

1. Create prompt: `agents/custom/<name>-agent.md`
2. Add department config in `scripts/run_department.py` (DEPARTMENT_CONFIG dict)
3. Create workflow: `.github/workflows/<name>.yml` with cron schedule
4. Add to `config/org-chart.json` under the right VP
5. Update this Team Roster
6. Run: `gh workflow run <name>.yml -R mindfulcrumb/gadgetgeeks-marketing-org` to test
