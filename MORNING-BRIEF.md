# Morning Brief — March 15, 2026

## What Got Done Yesterday (March 14)

1. **Blog Published**: "Best Refurbished iPhone in 2026 (Tested & Ranked)" — LIVE with header image at gadgetgeekspro.com/blogs/news/best-refurbished-iphone-2026-tested-ranked
2. **Blog Pipeline Fixed**: SCRIBE → QUILL → PRESS now runs end-to-end. Was broken because `blog_writer`, `blog_qa`, `blog_publish` were missing from `DEPARTMENT_CONFIG` in `run_department.py`. Fixed.
3. **Dashboard Restored**: God Mode + Mission Control merged into single page. Blog Pipeline, Approval Queue (with APPROVE/REJECT buttons), and Comms Center restored to sidebar. All 21 agents now visible in animated view. Staff count fixed (27 → 21).
4. **Telegram Bot Fixed**: Python `poll_and_respond()` was calling `deleteWebhook` every 5 minutes, killing the Cloudflare Worker webhook. Removed. Webhook re-registered via new `setup-telegram-webhook.yml` workflow.
5. **Image Gen Prompt Updated**: Added phone orientation checks — no more mirrored camera modules.
6. **OPENAI_API_KEY** added as fallback to `fix-blog-image.yml` workflow.
7. **New workflow**: `fix-blog-image-direct.yml` — bypasses broken `_cmd_fix_image` blogs array lookup.

---

## What's Broken — Needs Fixing

### FIXED LAST NIGHT (March 14 late)

- **6 missing departments** — `standup`, `retro`, `board_meeting`, `night_ops`, `google_trends`, `analytics` all added to `DEPARTMENT_CONFIG`. Total departments: 23. All scheduled workflows should now succeed.
- **`_cmd_fix_image` bug** — fixed blog lookup to handle single-blog pipeline format. Original fix-blog-image workflow now works.
- **POSTIZ_API_KEY** — already in GitHub secrets since March 13. Social posting should be working.

### REMAINING — NEEDS ATTENTION

| Issue | Details | Impact |
|-------|---------|--------|
| **18 pending queue items** | Piling up with no approvals — includes SEO briefs, social content, infrastructure fixes | Content backlog growing daily |

### MEDIUM PRIORITY

| Issue | Details |
|-------|---------|
| **Competitor pricing vs plug.tech** | Still not done from previous sessions |
| **Gemini API stability** | Was 403 for 48+ hours, works now, but no alerting if it goes down again |
| **Queue item cleanup** | Some items are stale (>48 hours), some have empty department/summary fields |
| **Evergreen Blog Writer** | Separate workflow (18:00 UTC) — need to verify it also works with fixed `DEPARTMENT_CONFIG` |

### LOW PRIORITY / NICE TO HAVE

| Issue | Details |
|-------|---------|
| **Canva pipeline** | `test-canva-pipeline.yml` exists but untested |
| **Creatify UGC batch** | Script exists at `scripts/creatify-batch.sh`, avatar IDs still placeholder |
| **Dashboard deploy** | Dashboard files are in repo but not hosted anywhere persistent |

---

## Queue Review (18 Pending)

Items that need your decision:

1. **SEO Brief**: "How to Buy Used Phones Online Safely" — full content brief ready, needs approval to go to SCRIBE
2. **Social**: TikTok behind-the-scenes video content — needs video production capability
3. **Social**: Reddit expansion strategy (r/frugal, r/technology, r/BuyItForLife)
4. **X-Intel**: iPhone 17e vs 15 Pro comparison post — trending topic, time-sensitive
5. **X-Intel**: Back Market tampering/security story — competitive angle
6. **SEO**: iPad collection page optimization
7. **Infrastructure**: Gemini API debug (may be resolved now)
8. **Infrastructure**: Postiz platform reconnection
9. **Night Ops**: Critical items pending >48 hours alert

---

## System Health at a Glance

| Component | Status |
|-----------|--------|
| Blog Pipeline (SCRIBE → QUILL → PRESS) | WORKING |
| Telegram Bot (Cloudflare Worker) | WORKING |
| Dashboard (God Mode + MC) | WORKING |
| Image Generation (Gemini + DALL-E fallback) | WORKING (was down, back up) |
| Social Media Posting (Postiz) | DEGRADED — no API key |
| 6 Department Workflows (standup/retro/night/trends/analytics/board) | FIXED — configs added |
| `_cmd_fix_image` (Telegram /fix_image) | FIXED — handles single-blog format |
| POSTIZ_API_KEY | ALREADY SET — in GH secrets since March 13 |
| Approval Queue | WORKING but 18 items unreviewed |

---

## Recommended Priority Order

1. ~~Fix 6 missing DEPARTMENT_CONFIG entries~~ DONE
2. ~~Fix _cmd_fix_image blog lookup bug~~ DONE
3. ~~POSTIZ_API_KEY~~ ALREADY SET
4. Review and approve/reject 18 queue items (10 min) — clear the backlog
5. Verify tonight's standup/night_ops/retro runs succeed with new configs
6. Competitor pricing analysis vs plug.tech
