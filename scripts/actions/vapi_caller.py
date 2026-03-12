#!/usr/bin/env python3
"""
Vapi.ai API wrapper for the GadgetGeeks Marketing Organization.
Handles outbound calling: create assistants, make calls, check outcomes.

Docs: https://docs.vapi.ai/api-reference/calls/create
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime, timezone

VAPI_BASE_URL = "https://api.vapi.ai"
REPO_ROOT = Path(__file__).parent.parent.parent


def _get_headers() -> dict:
    """Get auth headers for Vapi API."""
    key = os.environ.get("VAPI_API_KEY", "")
    if not key:
        raise Exception("VAPI_API_KEY not set")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Assistant management
# ---------------------------------------------------------------------------

def create_assistant(
    name: str,
    system_prompt: str,
    first_message: str,
    voice_provider: str = "11labs",
    voice_id: str = "burt",
    model: str = "gpt-4o",
    end_call_phrases: list = None,
    max_duration_seconds: int = 300,
) -> dict:
    """Create a Vapi assistant for phone calls.

    Args:
        name: Assistant name
        system_prompt: The instructions/persona for the assistant
        first_message: What the assistant says when the call connects
        voice_provider: Voice provider (11labs, playht, deepgram, etc.)
        voice_id: Voice ID from the provider
        model: LLM model to use
        end_call_phrases: Phrases that trigger call end
        max_duration_seconds: Max call length (default 5 min)
    """
    payload = {
        "name": name,
        "model": {
            "provider": "openai",
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                }
            ],
        },
        "voice": {
            "provider": voice_provider,
            "voiceId": voice_id,
            "speed": 0.9,
            "stability": 0.6,
            "similarityBoost": 0.8,
        },
        "firstMessage": first_message,
        "endCallPhrases": end_call_phrases or [
            "goodbye", "have a good day", "not interested",
            "take me off your list", "do not call",
        ],
        "maxDurationSeconds": max_duration_seconds,
        "silenceTimeoutSeconds": 30,
        "responseDelaySeconds": 1.2,
        "backgroundSound": "office",
        "voicemailDetection": {
            "enabled": True,
            "provider": "twilio",
        },
    }

    resp = requests.post(
        f"{VAPI_BASE_URL}/assistant",
        headers=_get_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def get_assistant(assistant_id: str) -> dict:
    """Get assistant details."""
    resp = requests.get(
        f"{VAPI_BASE_URL}/assistant/{assistant_id}",
        headers=_get_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def list_assistants() -> list:
    """List all assistants."""
    resp = requests.get(
        f"{VAPI_BASE_URL}/assistant",
        headers=_get_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Phone number management
# ---------------------------------------------------------------------------

def list_phone_numbers() -> list:
    """List all phone numbers."""
    resp = requests.get(
        f"{VAPI_BASE_URL}/phone-number",
        headers=_get_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Call management
# ---------------------------------------------------------------------------

def create_call(
    assistant_id: str,
    phone_number_id: str,
    customer_number: str,
    schedule_at: str = None,
) -> dict:
    """Create a single outbound call.

    Args:
        assistant_id: ID of the Vapi assistant to use
        phone_number_id: ID of your Vapi phone number
        customer_number: Customer's phone number (E.164 format: +1XXXXXXXXXX)
        schedule_at: ISO datetime to schedule call (optional)
    """
    payload = {
        "assistantId": assistant_id,
        "phoneNumberId": phone_number_id,
        "customer": {
            "number": customer_number,
        },
    }

    if schedule_at:
        payload["schedulePlan"] = {"earliestAt": schedule_at}

    resp = requests.post(
        f"{VAPI_BASE_URL}/call",
        headers=_get_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def create_batch_calls(
    assistant_id: str,
    phone_number_id: str,
    customer_numbers: list,
    schedule_at: str = None,
) -> dict:
    """Create batch outbound calls to multiple customers.

    Args:
        assistant_id: ID of the Vapi assistant
        phone_number_id: ID of your Vapi phone number
        customer_numbers: List of phone numbers (E.164 format)
        schedule_at: ISO datetime to schedule calls
    """
    customers = [{"number": n} for n in customer_numbers]

    payload = {
        "assistantId": assistant_id,
        "phoneNumberId": phone_number_id,
        "customers": customers,
    }

    if schedule_at:
        payload["schedulePlan"] = {"earliestAt": schedule_at}

    resp = requests.post(
        f"{VAPI_BASE_URL}/call",
        headers=_get_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def get_call(call_id: str) -> dict:
    """Get call details and outcome."""
    resp = requests.get(
        f"{VAPI_BASE_URL}/call/{call_id}",
        headers=_get_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def list_calls(limit: int = 50) -> list:
    """List recent calls."""
    resp = requests.get(
        f"{VAPI_BASE_URL}/call",
        headers=_get_headers(),
        params={"limit": limit},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# GadgetGeeks-specific call scripts
# ---------------------------------------------------------------------------

CALL_SCRIPTS = {
    "abandoned_cart": {
        "name": "GadgetGeeks Abandoned Cart Recovery",
        "first_message": "Hey, how's it going? ... This is Xavier, from Gadget Geeks Pro. Quick heads up this call may be recorded. ... I saw you were checking out some phones on our site and wanted to see if you had any questions?",
        "system_prompt": """You are Xavier, a friendly sales associate at Gadget Geeks Pro, a refurbished phone store.

You're calling customers who left items in their cart. Your goal is to answer any questions and help them complete their purchase.

PERSONALITY:
- Friendly, casual, not pushy
- You genuinely want to help, not hard-sell
- If they're not interested, accept it gracefully
- Sound like a real person, not a script reader

CALL FLOW:
1. Introduce yourself briefly
2. Mention you noticed they were browsing (don't say "abandoned cart")
3. Ask if they had questions about the phone they were looking at
4. Address common concerns: warranty, condition, activation lock, returns
5. If interested: offer to hold the item or share a discount code
6. If not interested: thank them and end the call politely

KEY SELLING POINTS:
- 90-day warranty on all devices
- 65-point inspection process
- Free returns within 30 days
- Activation lock verified clear on every phone
- Prices 40-60% less than new

RULES:
- NEVER be pushy or aggressive
- If they say "not interested" or "don't call again", immediately respect that
- Keep the call under 3 minutes
- Don't make promises you can't keep
- If they ask technical questions you can't answer, offer to email them details
""",
    },

    "review_request": {
        "name": "GadgetGeeks Review Request",
        "first_message": "Hey there! ... It's Xavier from Gadget Geeks Pro. This call may be recorded, just so you know. ... I'm just calling to check in — how's the new phone treating you?",
        "system_prompt": """You are Xavier, a customer success associate at Gadget Geeks Pro.

You're calling customers who purchased 7-14 days ago to check on their experience and request a review.

PERSONALITY:
- Warm, genuine, appreciative
- You care about their experience first, review second
- If they have issues, prioritize solving them

CALL FLOW:
1. Introduce yourself
2. Ask how the phone is working out
3. If happy: ask if they'd leave a quick review (explain it helps other buyers)
4. If issues: take notes, offer solutions (warranty, support email, returns)
5. Thank them regardless

RULES:
- Device satisfaction comes first, review request second
- If they have ANY issue, focus on resolving it
- Keep under 2 minutes
- Never pressure for a review
""",
    },

    "winback": {
        "name": "GadgetGeeks Win-Back",
        "first_message": "Hey, what's up? ... It's Xavier from Gadget Geeks Pro. This call may be recorded just so you know. ... It's been a minute since we talked — I just wanted to let you know we got some crazy deals right now on phones.",
        "system_prompt": """You are Xavier, a sales associate at Gadget Geeks Pro.

You're calling customers who haven't purchased in 60+ days to re-engage them.

PERSONALITY:
- Upbeat but not over-the-top
- Informative, sharing genuine deals
- Respectful of their time

CALL FLOW:
1. Brief intro — acknowledge it's been a while
2. Share one specific deal relevant to their purchase history
3. Mention any new arrivals (iPhone 15 refurbished, Galaxy S24, etc.)
4. If interested: direct them to the website or offer to text a link
5. If not: thank them, ask if they'd like to stay on the text list for deals

RULES:
- One call attempt only — if voicemail, leave a brief message
- Keep under 2 minutes
- Don't push if they're not interested
""",
    },

    "direct_instruction": {
        "name": "GadgetGeeks Direct Outreach",
        "first_message": "Hey, how are you doing? ... This is Xavier from Gadget Geeks Pro. Just a heads up this call may be recorded. ... I'm reaching out because we've got some pretty solid deals on phones right now and thought you might wanna hear about them.",
        "system_prompt": """You are Xavier, a friendly sales associate at Gadget Geeks Pro, a refurbished phone store.

You're calling someone the boss personally wants you to reach out to. Be natural and conversational.

PERSONALITY:
- Friendly, genuine, enthusiastic about phones
- You know your stuff about refurbished devices
- Not pushy — you're sharing something cool
- Sound like a real person having a conversation

CALL FLOW:
1. Introduce yourself briefly
2. Ask if they're in the market for a phone or know someone who is
3. Share what makes refurbished phones a smart buy
4. Address concerns: warranty, condition, battery health, returns
5. If interested: direct them to the website or offer to text details
6. If not: thank them, keep it light

KEY SELLING POINTS:
- 90-day warranty on all devices
- 65-point inspection process
- Battery health 80%+ guaranteed
- Free returns within 30 days
- Prices 40-60% less than new
- Activation lock verified clear on every phone

RULES:
- NEVER be pushy
- If they say "not interested" or "don't call again", respect that immediately
- Keep under 3 minutes
- Be genuine — you actually like what you're selling
""",
    },

    "b2b_outreach": {
        "name": "GadgetGeeks B2B Outreach",
        "first_message": "Hi there. ... This is Xavier from Gadget Geeks Pro, this call may be recorded. ... We work with businesses on refurbished phone deals at wholesale pricing. Does your company use mobile devices for your team?",
        "system_prompt": """You are Xavier, the B2B sales lead at Gadget Geeks Pro.

You're cold-calling businesses to pitch bulk refurbished phone deals.

PERSONALITY:
- Professional but approachable
- Knowledgeable about business phone needs
- Solution-oriented

CALL FLOW:
1. Introduce yourself and the company
2. Ask about their current phone setup (how many employees, what devices)
3. Present the value prop: 40-60% savings on refurbished, same performance
4. Mention: bulk pricing, warranty, dedicated support
5. If interested: schedule a follow-up call or email quote
6. If not: thank them, ask if you can send info for future reference

KEY B2B POINTS:
- Volume pricing starts at 10+ units
- Custom grading to match budget
- Dedicated account manager for 25+ units
- Same 90-day warranty, extendable to 1 year
- MDM-ready devices (wiped, ready for enrollment)

RULES:
- Respect gatekeepers — be polite to receptionists
- If they say they handle purchasing differently, ask who to contact
- Keep initial call under 3 minutes
- Always offer a follow-up email as a lower-commitment option
""",
    },
}


def get_or_create_assistant(script_type: str) -> str:
    """Get existing assistant ID or create one for the given script type.

    Returns the assistant ID.
    """
    config_path = REPO_ROOT / "config" / "vapi.json"
    config = {}
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))

    # Check if we already have an assistant for this type
    assistants = config.get("assistants", {})
    if script_type in assistants:
        return assistants[script_type]

    # Create new assistant
    script = CALL_SCRIPTS.get(script_type)
    if not script:
        raise Exception(f"Unknown script type: {script_type}")

    result = create_assistant(
        name=script["name"],
        system_prompt=script["system_prompt"],
        first_message=script["first_message"],
    )

    # Save assistant ID
    assistants[script_type] = result["id"]
    config["assistants"] = assistants
    config["updated_at"] = datetime.now(timezone.utc).isoformat()
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    return result["id"]


# ---------------------------------------------------------------------------
# Call list management
# ---------------------------------------------------------------------------

def load_call_list() -> dict:
    """Load the current call list."""
    path = REPO_ROOT / "departments" / "dialer" / "call-list.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"pending": [], "completed": [], "stats": {"total_calls": 0, "total_connected": 0, "total_interested": 0}}


def save_call_list(data: dict):
    """Save the call list."""
    path = REPO_ROOT / "departments" / "dialer" / "call-list.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def execute_approved_calls() -> list:
    """Execute all approved calls from the call list.

    Returns list of call results.
    """
    config_path = REPO_ROOT / "config" / "vapi.json"
    if not config_path.exists():
        print("  No vapi.json config found")
        return []

    config = json.loads(config_path.read_text(encoding="utf-8"))
    phone_number_id = config.get("phone_number_id", "")
    if not phone_number_id:
        print("  No phone_number_id configured in vapi.json")
        return []

    call_list = load_call_list()
    results = []

    for item in call_list.get("pending", []):
        if item.get("status") != "approved":
            continue

        script_type = item.get("script_type", "abandoned_cart")
        customer_number = item.get("phone_number")

        if not customer_number:
            continue

        try:
            assistant_id = get_or_create_assistant(script_type)
            call_result = create_call(
                assistant_id=assistant_id,
                phone_number_id=phone_number_id,
                customer_number=customer_number,
            )
            item["status"] = "called"
            item["call_id"] = call_result.get("id")
            item["called_at"] = datetime.now(timezone.utc).isoformat()
            results.append({"number": customer_number, "call_id": call_result.get("id"), "status": "initiated"})
            print(f"  Called: {customer_number} ({script_type})")

            # Notify boss via Telegram
            try:
                from scripts.actions.telegram_bot import send_message
                customer_name = item.get("customer_name", "Unknown")
                send_message(
                    f"\U0001F4DE <b>XAVIER — Call Initiated</b>\n\n"
                    f"\U0001F464 <b>{customer_name}</b>\n"
                    f"\U0001F4F1 <code>{customer_number}</code>\n"
                    f"\U0001F3AF Script: {script_type}\n"
                    f"\U0001F194 <code>{call_result.get('id', '?')}</code>\n\n"
                    f"\u2705 Call is ringing now."
                )
            except Exception as tg_err:
                print(f"  Telegram notify error: {tg_err}")

        except Exception as e:
            item["status"] = "error"
            item["error"] = str(e)
            results.append({"number": customer_number, "error": str(e)})
            print(f"  ERROR calling {customer_number}: {e}")

            # Notify boss of failed call
            try:
                from scripts.actions.telegram_bot import send_message
                customer_name = item.get("customer_name", "Unknown")
                send_message(
                    f"\u274C <b>XAVIER — Call Failed</b>\n\n"
                    f"\U0001F464 <b>{customer_name}</b>\n"
                    f"\U0001F4F1 <code>{customer_number}</code>\n"
                    f"Error: {str(e)[:200]}"
                )
            except Exception:
                pass

    # Move completed items
    still_pending = []
    for item in call_list.get("pending", []):
        if item.get("status") in ("called", "error"):
            call_list.setdefault("completed", []).append(item)
            call_list["stats"]["total_calls"] = call_list["stats"].get("total_calls", 0) + 1
        else:
            still_pending.append(item)
    call_list["pending"] = still_pending

    save_call_list(call_list)
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "list-numbers":
        numbers = list_phone_numbers()
        for n in numbers:
            print(f"  {n.get('id')} — {n.get('number', n.get('phoneNumber', '?'))}")
    elif len(sys.argv) > 1 and sys.argv[1] == "list-assistants":
        assistants = list_assistants()
        for a in assistants:
            print(f"  {a.get('id')} — {a.get('name', '?')}")
    elif len(sys.argv) > 1 and sys.argv[1] == "execute":
        results = execute_approved_calls()
        print(f"Executed {len(results)} call(s)")
    else:
        print("Usage: python vapi_caller.py [list-numbers|list-assistants|execute]")
