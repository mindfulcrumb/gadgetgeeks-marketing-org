#!/usr/bin/env bash
# ============================================================================
# GadgetGeeks Telegram Webhook Setup
#
# This script:
#   1. Deploys the Cloudflare Worker
#   2. Sets the Telegram webhook URL to point to the Worker
#   3. Verifies the webhook is active
#
# Prerequisites:
#   - Node.js / npm installed
#   - Cloudflare account (free tier works)
#   - wrangler CLI: npm install -g wrangler
#   - Logged into wrangler: wrangler login
#
# Required environment variables (or set as CF Worker secrets):
#   TELEGRAM_BOT_TOKEN — Telegram bot token for @GGP_MA_Bot
#   GH_TOKEN           — GitHub PAT with repo + workflow scope
#   CF_API_TOKEN        — (optional) Cloudflare API token for non-interactive deploy
#
# Usage:
#   chmod +x scripts/setup-webhook.sh
#   TELEGRAM_BOT_TOKEN=your_token GH_TOKEN=your_pat ./scripts/setup-webhook.sh
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "============================================"
echo "  GadgetGeeks Telegram Webhook Deployment"
echo "============================================"
echo ""

# --- 1. Check prerequisites ---
if ! command -v npx &> /dev/null; then
    echo -e "${RED}ERROR: npx not found. Install Node.js first.${NC}"
    exit 1
fi

if ! command -v wrangler &> /dev/null && ! npx wrangler --version &> /dev/null; then
    echo -e "${YELLOW}Installing wrangler...${NC}"
    npm install -g wrangler
fi

# --- 2. Check required env vars ---
if [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then
    echo -e "${RED}ERROR: TELEGRAM_BOT_TOKEN not set.${NC}"
    echo "Export it: export TELEGRAM_BOT_TOKEN=your_bot_token"
    exit 1
fi

if [ -z "${GH_TOKEN:-}" ]; then
    echo -e "${YELLOW}WARNING: GH_TOKEN not set. Action commands (/run, /boss, etc.) won't work.${NC}"
fi

# --- 3. Deploy the Cloudflare Worker ---
echo -e "${GREEN}[1/4] Deploying Cloudflare Worker...${NC}"
cd "$SCRIPT_DIR"
npx wrangler deploy

# Capture the worker URL from wrangler output
# Default pattern: https://gadgetgeeks-telegram-webhook.<account>.workers.dev
WORKER_URL=$(npx wrangler deployments list --json 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    # Try to extract URL
    print('')
except:
    print('')
" 2>/dev/null || echo "")

# If we couldn't auto-detect, construct it
if [ -z "$WORKER_URL" ]; then
    # Ask the user or use the standard pattern
    echo ""
    echo -e "${YELLOW}Could not auto-detect worker URL.${NC}"
    echo "Check the wrangler deploy output above for the URL."
    echo "It should look like: https://gadgetgeeks-telegram-webhook.YOUR_SUBDOMAIN.workers.dev"
    echo ""
    read -p "Paste your Worker URL here: " WORKER_URL
fi

if [ -z "$WORKER_URL" ]; then
    echo -e "${RED}ERROR: No Worker URL. Cannot set webhook.${NC}"
    exit 1
fi

# --- 4. Set Worker secrets ---
echo ""
echo -e "${GREEN}[2/4] Setting Worker secrets...${NC}"
echo "$TELEGRAM_BOT_TOKEN" | npx wrangler secret put TELEGRAM_BOT_TOKEN

if [ -n "${GH_TOKEN:-}" ]; then
    echo "$GH_TOKEN" | npx wrangler secret put GH_TOKEN
fi

# --- 5. Set Telegram webhook ---
echo ""
echo -e "${GREEN}[3/4] Setting Telegram webhook...${NC}"
WEBHOOK_RESPONSE=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
    -d "url=${WORKER_URL}" \
    -d "allowed_updates=[\"message\",\"edited_message\"]" \
    -d "drop_pending_updates=false")

echo "Telegram response: $WEBHOOK_RESPONSE"

# Check if it worked
OK=$(echo "$WEBHOOK_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ok', False))" 2>/dev/null || echo "false")

if [ "$OK" != "True" ]; then
    echo -e "${RED}ERROR: Failed to set webhook. Check your bot token.${NC}"
    exit 1
fi

# --- 6. Verify webhook ---
echo ""
echo -e "${GREEN}[4/4] Verifying webhook...${NC}"
WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo")
echo "Webhook info:"
echo "$WEBHOOK_INFO" | python3 -m json.tool 2>/dev/null || echo "$WEBHOOK_INFO"

echo ""
echo "============================================"
echo -e "${GREEN}  DEPLOYMENT COMPLETE${NC}"
echo "============================================"
echo ""
echo "Worker URL:  $WORKER_URL"
echo "Bot:         @GGP_MA_Bot"
echo "Mode:        Webhook (instant responses)"
echo ""
echo "The bot now responds INSTANTLY to messages."
echo "The old polling workflow (telegram-poll.yml) is"
echo "still active as a fallback but won't receive"
echo "messages while the webhook is set."
echo ""
echo "To revert to polling mode:"
echo "  curl 'https://api.telegram.org/bot\${TELEGRAM_BOT_TOKEN}/deleteWebhook'"
echo ""
echo "To check webhook status:"
echo "  curl 'https://api.telegram.org/bot\${TELEGRAM_BOT_TOKEN}/getWebhookInfo'"
echo ""
