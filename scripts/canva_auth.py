#!/usr/bin/env python3
"""
One-time Canva OAuth flow to get an access token.

Usage:
  python scripts/canva_auth.py

1. Opens your browser to authorize the Canva integration
2. Canva redirects to localhost with a code
3. Exchanges the code for an access token
4. Prints the token — add it to GitHub secrets with:
   gh secret set CANVA_ACCESS_TOKEN -R mindfulcrumb/gadgetgeeks-marketing-org
"""

import hashlib
import http.server
import json
import os
import secrets
import sys
import urllib.parse
import webbrowser

import requests

# --- Configuration ---
CLIENT_ID = os.environ.get("CANVA_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("CANVA_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:3456/callback"
SCOPES = "design:content:read design:content:write asset:read asset:write"
TOKEN_URL = "https://api.canva.com/rest/v1/oauth/token"
AUTH_URL = "https://www.canva.com/api/oauth/authorize"

# --- PKCE ---
code_verifier = secrets.token_urlsafe(64)[:128]
code_challenge = (
    hashlib.sha256(code_verifier.encode())
    .digest()
    .__class__
    .__bases__[0]
    .__subclasses__()[0]
)
# Simpler PKCE
import base64
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b"=").decode()

auth_code = None


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Success!</h1>"
                b"<p>Authorization code received. You can close this tab.</p>"
                b"</body></html>"
            )
        else:
            error = params.get("error", ["unknown"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"<html><body><h1>Error</h1><p>{error}</p></body></html>".encode()
            )

    def log_message(self, format, *args):
        pass  # Suppress request logs


def main():
    # Build authorization URL
    state = secrets.token_urlsafe(32)
    auth_params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })
    full_auth_url = f"{AUTH_URL}?{auth_params}"

    print("=" * 60)
    print("  CANVA OAUTH — GET ACCESS TOKEN")
    print("=" * 60)
    print()
    print("Opening your browser to authorize the Canva integration...")
    print(f"If it doesn't open, go to:\n{full_auth_url}")
    print()

    # Start local server
    server = http.server.HTTPServer(("localhost", 3456), CallbackHandler)
    webbrowser.open(full_auth_url)

    print("Waiting for authorization callback on http://localhost:3456 ...")
    while auth_code is None:
        server.handle_request()

    server.server_close()
    print(f"\nAuthorization code received!")

    # Exchange code for token
    print("Exchanging code for access token...")
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier,
        },
        auth=(CLIENT_ID, CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )

    if resp.status_code != 200:
        print(f"\nERROR: Token exchange failed ({resp.status_code})")
        print(resp.text)
        sys.exit(1)

    data = resp.json()
    access_token = data.get("access_token", "")
    refresh_token = data.get("refresh_token", "")
    expires_in = data.get("expires_in", 0)

    print()
    print("=" * 60)
    print("  ACCESS TOKEN (copy this)")
    print("=" * 60)
    print(f"\n{access_token}\n")
    print(f"Expires in: {expires_in} seconds ({expires_in // 3600} hours)")

    if refresh_token:
        print(f"\nRefresh token (save this for token renewal):")
        print(f"{refresh_token}")

    print()
    print("Now run:")
    print(f'  gh secret set CANVA_ACCESS_TOKEN --body "{access_token[:20]}..." -R mindfulcrumb/gadgetgeeks-marketing-org')
    print()

    # Save tokens locally for convenience
    tokens_path = os.path.join(os.path.dirname(__file__), ".canva-tokens.json")
    with open(tokens_path, "w") as f:
        json.dump({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in,
        }, f, indent=2)
    print(f"Tokens saved to {tokens_path} (gitignored)")


if __name__ == "__main__":
    main()
