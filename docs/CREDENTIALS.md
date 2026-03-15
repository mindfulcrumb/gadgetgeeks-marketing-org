# Credentials Reference

All secrets are stored as **GitHub Repository Secrets** in `mindfulcrumb/gadgetgeeks-marketing-org`.

Never put credentials in source code. Scripts use `os.environ.get("KEY", "")` with empty defaults.

---

## GitHub Secrets

| Secret | Purpose | Used by | Rotation |
|--------|---------|---------|----------|
| `ANTHROPIC_API_KEY` | Claude API (Sonnet/Opus) — powers all agents | All department workflows | No expiry |
| `TELEGRAM_BOT_TOKEN` | Telegram bot @GGP_MA_Bot | telegram-poll.yml, all dept notifications | No expiry |
| `SHOPIFY_CLIENT_ID` | Shopify app client ID | blog-publish, telegram-poll, dialer | No expiry |
| `SHOPIFY_CLIENT_SECRET` | Shopify app client secret | blog-publish, telegram-poll, dialer | No expiry |
| `SHOPIFY_STORE` | Store domain (gadgetgeekspro.myshopify.com) | Shopify API calls | Static |
| `SHOPIFY_ACCESS_TOKEN` | Pre-generated access token (backup) | Direct API calls | 24h expiry |
| `GEMINI_API_KEY` | Google Gemini Imagen 4 — blog header images | blog-publish, telegram-poll | No expiry |
| `RESEND_API_KEY` | Resend email API | gm-queue (sends approved emails) | No expiry |
| `X_BEARER_TOKEN` | X/Twitter API v2 bearer token | x-intel.yml | No expiry |
| `VAPI_API_KEY` | Vapi.ai phone calling API | dialer-execute.yml | No expiry |
| `GOOGLE_SERVICE_ACCOUNT_KEY` | Google Cloud service account JSON key | analytics.yml | No expiry |
| `GA4_PROPERTY_ID` | GA4 property ID (527689586) | analytics.yml | Static |
| `GSC_SITE_URL` | Search Console site URL | analytics.yml | Static |

---

## Shopify Token Flow

Shopify tokens expire every **24 hours**. Workflows that need Shopify access generate a fresh token:

```bash
curl -s -X POST "https://gadgetgeekspro.myshopify.com/admin/oauth/access_token" \
  -d "grant_type=client_credentials" \
  -d "client_id=$SHOPIFY_CLIENT_ID" \
  -d "client_secret=$SHOPIFY_CLIENT_SECRET"
```

This is handled automatically in workflow YAML files via the "Get fresh Shopify token" step.

---

## Which Workflows Need Which Secrets

| Workflow | ANTHROPIC | TELEGRAM | SHOPIFY_* | GEMINI | RESEND | X_BEARER | VAPI | GOOGLE_* |
|----------|-----------|----------|-----------|--------|--------|----------|------|----------|
| All departments | x | x | | | | | | |
| analytics | x | x | | | | | | x |
| telegram-poll | | x | x | x | | | | |
| blog-publish | x | x | x | x | | | | |
| x-intel | x | x | | | | x | | |
| gm-queue | x | x | | | x | | | |
| dialer-execute | | x | | | | | x | |

---

## External Services

| Service | Dashboard | What it does |
|---------|-----------|-------------|
| Anthropic | console.anthropic.com | Claude API — all agent intelligence |
| Telegram | t.me/GGP_MA_Bot | Command center, notifications |
| Shopify | gadgetgeekspro.myshopify.com/admin | Store, products, blog, theme |
| Google Cloud | console.cloud.google.com | Gemini Imagen 4 image generation |
| Resend | resend.com | Transactional + marketing emails |
| Vapi | dashboard.vapi.ai | AI phone calling (Xavier) |
| X/Twitter | developer.x.com | Social intelligence API |
| Postiz | (self-hosted/SaaS) | Social media cross-posting |
| GitHub | github.com/mindfulcrumb/gadgetgeeks-marketing-org | Code, CI/CD, secrets |

---

## Adding a New Secret

```bash
# Set a secret
gh secret set SECRET_NAME -R mindfulcrumb/gadgetgeeks-marketing-org

# Verify it exists
gh secret list -R mindfulcrumb/gadgetgeeks-marketing-org

# Use in workflow YAML
env:
  SECRET_NAME: ${{ secrets.SECRET_NAME }}
```

---

## Security Rules

1. **Never hardcode credentials** — INC-002 (March 11) logged this exact mistake
2. Scripts must fail explicitly when a key is missing — no silent fallbacks
3. Shopify tokens are masked in GitHub Actions logs (`::add-mask::`)
4. `config/telegram.json` stores `chat_id` but NOT `bot_token` (that's in secrets)
5. `config/vapi.json` stores `phone_number_id` but NOT `api_key` (that's in secrets)
