#!/usr/bin/env python3
"""
One-time VAPI account audit — list assistants, delete non-GadgetGeeks ones,
create fresh assistants for our call scripts.
"""
import os
import json
import requests

VAPI_BASE = "https://api.vapi.ai"
KEY = os.environ.get("VAPI_API_KEY", "")
HEADERS = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}


def api(method, path, payload=None):
    url = f"{VAPI_BASE}{path}"
    r = requests.request(method, url, headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    return r.json() if r.text else {}


def main():
    if not KEY:
        print("ERROR: VAPI_API_KEY not set")
        return

    # 1. List all assistants
    print("=== CURRENT ASSISTANTS ===")
    assistants = api("GET", "/assistant")
    for a in assistants:
        print(f"  ID: {a['id']}")
        print(f"  Name: {a.get('name', '?')}")
        model = a.get("model", {})
        msgs = model.get("messages", [])
        if msgs:
            content = msgs[0].get("content", "")[:200]
            print(f"  System prompt preview: {content}")
        print(f"  First message: {a.get('firstMessage', '?')[:150]}")
        print()

    # 2. List phone numbers
    print("=== PHONE NUMBERS ===")
    numbers = api("GET", "/phone-number")
    for n in numbers:
        print(f"  ID: {n.get('id')} — {n.get('number', n.get('phoneNumber', '?'))}")
        if n.get('assistantId'):
            print(f"  Linked assistant: {n.get('assistantId')}")
        print()

    # 3. Delete ALL existing assistants (they have wrong info)
    print("=== CLEANING UP ===")
    for a in assistants:
        name = a.get("name", "?")
        print(f"  Deleting assistant: {a['id']} ({name})")
        try:
            api("DELETE", f"/assistant/{a['id']}")
            print(f"    Deleted.")
        except Exception as e:
            print(f"    Error: {e}")

    # 4. Create fresh GadgetGeeks assistants
    from vapi_caller import CALL_SCRIPTS, create_assistant

    print("\n=== CREATING GADGETGEEKS ASSISTANTS ===")
    new_ids = {}
    for script_type, script in CALL_SCRIPTS.items():
        print(f"  Creating: {script['name']}")
        result = create_assistant(
            name=script["name"],
            system_prompt=script["system_prompt"],
            first_message=script["first_message"],
        )
        new_ids[script_type] = result["id"]
        print(f"    ID: {result['id']}")

    # 5. Update config
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "vapi.json")
    config = json.loads(open(config_path).read())
    config["assistants"] = new_ids
    open(config_path, "w").write(json.dumps(config, indent=2))
    print(f"\n  Updated config/vapi.json with {len(new_ids)} assistant IDs")

    print("\n=== DONE ===")
    print("All assistants are now Gadget Geeks Pro (Xavier).")


if __name__ == "__main__":
    main()
