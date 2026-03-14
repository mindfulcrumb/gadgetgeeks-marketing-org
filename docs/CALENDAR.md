# CALENDAR

> Every scheduled task across the GadgetGeeks Marketing Org
> 37 workflows | 3 shifts | 24/7 coverage

---

## DAILY TIMELINE (UTC)

### NIGHT SHIFT — THE WATCH (20:00 - 05:59)

| Time | Agent | Event | Workflow | Frequency |
|------|-------|-------|----------|-----------|
| 00:00 | SENTINEL | Midnight health check | `night-ops.yml` | Daily |
| 03:00 | SENTINEL | Pre-dawn health check | `night-ops.yml` | Daily |
| 05:00 | SENTINEL | Pre-dawn prep — collect metrics, check APIs | `night-ops.yml` | Daily |
| 05:30 | SENTINEL | Night-to-morning handoff notes | `night-ops.yml` | Daily |

---

### MORNING SHIFT — THE BUILD (06:00 - 13:59)

| Time | Agent | Event | Workflow | Frequency |
|------|-------|-------|----------|-----------|
| 05:17 | PIXEL | Weekly SEO deep audit + content gaps | `seo-weekly.yml` | **Mon only** |
| 06:00 | CHIEF | Morning Standup — all-dept status | `morning-standup.yml` | Daily |
| 06:00 | TREND | Google Trends scan — rising queries | `google-trends.yml` | Daily |
| 06:23 | PIXEL | Daily SEO scan — keyword opportunities | `seo-daily.yml` | Daily |
| 06:30 | CHIEF | Weekly Board Meeting | `weekly-board.yml` | **Mon only** |
| 07:00 | ECHO | X Intelligence scan | `x-intel.yml` | Daily |
| 07:00 | BOT | Daily Telegram summary to boss | `telegram-summary.yml` | Daily |
| 07:03 | GM | Weekly Performance Report | `gm-report.yml` | **Fri only** |
| 07:30 | SIGNAL | GA/GSC analytics optimization | `analytics.yml` | Daily |
| 07:41 | Content | Daily content brief generation | `content.yml` | Daily |
| 08:19 | LENS | Generate 10 image prompts | `image-prompts.yml` | Daily |
| 08:49 | FOCUS | QA all 10 prompts (17 checks) | `prompt-qa.yml` | Daily |
| 08:53 | BEACON | Email campaign design + queue | `email.yml` | **Tue/Thu** |
| 08:55 | Gemini | Generate images from approved prompts | `image-generate.yml` | Daily |
| 09:25 | CANVAS | Design 10 branded Canva posts | `canva-post.yml` | Daily |
| 09:45 | VIBE | Morning social posts (1-2 posts) | `social-morning.yml` | Daily |
| 10:47 | SCOUT | Market intel — competitors + trends | `intel.yml` | **Mon/Thu** |
| 11:29 | OPTIMIZER | CRO audit — conversion analysis | `cro.yml` | **Wed only** |
| 12:00 | SCRIBE | Write trending blog (AM slot) | `blog-writer.yml` | Daily |
| 13:00 | QUILL | Blog QA — 25-check copy audit | `blog-qa.yml` | Daily |

---

### AFTERNOON SHIFT — THE PUSH (14:00 - 19:59)

| Time | Agent | Event | Workflow | Frequency |
|------|-------|-------|----------|-----------|
| 14:15 | XAVIER | Build call list from Shopify | `dialer.yml` | **Weekdays** |
| 14:30 | PRESS | Blog publish — queue for approval | `blog-publish.yml` | Daily |
| 15:00 | SYSTEM | Blog status report to Telegram | `blog-status-report.yml` | Daily |
| 15:45 | XAVIER | Execute approved calls (Vapi.ai) | `dialer-execute.yml` | **Weekdays** |
| 16:37 | VIBE | Afternoon engagement check | `social-afternoon.yml` | Daily |
| 18:00 | SCRIBE | Write evergreen blog (PM slot) | `blog-writer-pm.yml` | Daily |
| 18:51 | GM | Daily queue processing | `gm-queue.yml` | Daily |
| 20:00 | CHIEF | Evening Retro + night handoff | `evening-retro.yml` | Daily |

---

### ALWAYS-ON

| Schedule | Agent | Event | Workflow |
|----------|-------|-------|----------|
| Every 5 min | Telegram Bot | Poll for boss commands | `telegram-poll.yml` |

---

## WEEKLY VIEW

### MONDAY
| Time | Agent | Event | Notes |
|------|-------|-------|-------|
| 05:17 | PIXEL | Weekly SEO deep audit | Content gap analysis, competitor SERPs |
| 06:00 | CHIEF | Morning Standup | + reads weekend data |
| 06:30 | CHIEF | **Weekly Board Meeting** | Org-wide strategy review (Opus model) |
| 10:47 | SCOUT | Market intel | Competitor analysis + trends |
| + all daily events | | | |

### TUESDAY
| Time | Agent | Event | Notes |
|------|-------|-------|-------|
| 08:53 | BEACON | Email campaign | Design + queue for approval |
| + all daily events | | | |

### WEDNESDAY
| Time | Agent | Event | Notes |
|------|-------|-------|-------|
| 11:29 | OPTIMIZER | CRO audit | Conversion analysis + experiments |
| + all daily events | | | |

### THURSDAY
| Time | Agent | Event | Notes |
|------|-------|-------|-------|
| 08:53 | BEACON | Email campaign | Design + queue for approval |
| 10:47 | SCOUT | Market intel | Competitor analysis + trends |
| + all daily events | | | |

### FRIDAY
| Time | Agent | Event | Notes |
|------|-------|-------|-------|
| 07:03 | GM | **Weekly Performance Report** | Full org KPIs, budget, strategy (Opus model) |
| + all daily events | | | |

### SATURDAY + SUNDAY
| Events | Notes |
|--------|-------|
| All daily events run | Content, social, SEO, blog pipeline, night ops |
| No dialer (XAVIER) | Weekdays only |
| No email (BEACON) | Tue/Thu only |
| No intel (SCOUT) | Mon/Thu only |
| No CRO (OPTIMIZER) | Wed only |
| No board meeting | Mon only |
| No GM report | Fri only |

---

## CRON SCHEDULE REFERENCE

All cron expressions from `.github/workflows/`:

```
# NIGHT SHIFT
00 00 * * *    night-ops.yml         SENTINEL midnight check
00 03 * * *    night-ops.yml         SENTINEL pre-dawn check
00 05 * * *    night-ops.yml         SENTINEL morning prep

# MORNING SHIFT
17 05 * * 1    seo-weekly.yml        PIXEL weekly audit (Mon)
00 06 * * *    morning-standup.yml   CHIEF standup
00 06 * * *    google-trends.yml    TREND trends scan
23 06 * * *    seo-daily.yml         PIXEL daily SEO
30 06 * * 1    weekly-board.yml      CHIEF board meeting (Mon)
00 07 * * *    x-intel.yml           ECHO X intel
00 07 * * *    telegram-summary.yml  BOT daily summary
03 07 * * 5    gm-report.yml         GM weekly report (Fri)
30 07 * * *    analytics.yml         SIGNAL analytics
41 07 * * *    content.yml           Content briefs
19 08 * * *    image-prompts.yml     LENS 10 prompts
49 08 * * *    prompt-qa.yml         FOCUS prompt QA
53 08 * * 2,4  email.yml             BEACON email (Tue/Thu)
55 08 * * *    image-generate.yml    Gemini images
25 09 * * *    canva-post.yml        CANVAS designs
45 09 * * *    social-morning.yml    VIBE morning posts
47 10 * * 1,4  intel.yml             SCOUT intel (Mon/Thu)
29 11 * * 3    cro.yml               OPTIMIZER CRO (Wed)
00 12 * * *    blog-writer.yml       SCRIBE daily blog
00 13 * * *    blog-qa.yml           QUILL blog QA

# AFTERNOON SHIFT
15 14 * * 1-5  dialer.yml            XAVIER call list (weekdays)
30 14 * * *    blog-publish.yml      PRESS blog publish
00 15 * * *    blog-status-report.yml SYSTEM blog report
45 15 * * 1-5  dialer-execute.yml    XAVIER calls (weekdays)
37 16 * * *    social-afternoon.yml  VIBE engagement
00 18 * * *    blog-writer-pm.yml   SCRIBE evergreen blog (PM)
51 18 * * *    gm-queue.yml          GM queue processing
00 20 * * *    evening-retro.yml     CHIEF retro

# ALWAYS-ON
*/5 * * * *    telegram-poll.yml     BOT command polling
```

---

## VISUAL TIMELINE

```
UTC  00    03    05  06  07  08  09  10  11  12  13  14  15  16  17  18  19  20
     |     |     |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
     SEN   SEN   SEN CHF ECH LEN CAN SCT OPT SCR QUL XAV BLG VIB         GM  CHF
     ───   ───   ──┤ │   │   │   │   │   │   │   │   │   │   │          │   │
     mid   pre   ──┤ SEO X   FOC VIB │   CRO │   │   │   PRS │          QUE RET
     chk   dawn  ──┘ │   │   │   │   │   w   │   │   DIL │   │          │   │
                     PIX TLG BEA │   INT     │   │   exe  STR │          │   │
                     │   │   t/h │   m/h     │   │        │   │          │   │
                     │   GEN │   │           │   │        │   │          │   │
                     SEW CON IMG │           │   │        │   │          │   │
                     mon     │   │           │   │        │   │          │   │
                             │   │           │   │        │   │          │   │
     ◀── NIGHT SHIFT ──▶◀──────── MORNING SHIFT ─────────▶◀── AFTERNOON ──▶◀─N─
```

---

## HOW TO ADD A SCHEDULED TASK

1. Create workflow: `.github/workflows/<name>.yml`
2. Add cron schedule in the `on.schedule` section
3. Add department to `scripts/run_department.py` DEPARTMENT_CONFIG
4. Update this Calendar
5. Test: `gh workflow run <name>.yml -R mindfulcrumb/gadgetgeeks-marketing-org`
