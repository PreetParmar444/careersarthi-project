"""
careersarthi/auth.py
──────────────────────
One-time OAuth consent flow for Gmail (readonly) + Calendar access.
Run this once locally; it writes a token file that inbox_tracker and
deadline_guardian reuse. Re-run any time to re-consent or rotate scopes.

Usage:
    python -m careersarthi.auth
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

# Narrowest scopes that satisfy the two agents that need Google access.
# Deliberately NOT requesting gmail.modify, gmail.send, or full calendar write.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",  # needed to create reminder events
]


def main() -> None:
    creds_path = os.getenv("GMAIL_CREDENTIALS_PATH", ".secrets/gmail_credentials.json")
    token_path = os.getenv("GMAIL_TOKEN_PATH", ".secrets/gmail_token.json")

    Path(token_path).parent.mkdir(parents=True, exist_ok=True)

    if not os.path.exists(creds_path):
        raise FileNotFoundError(
            f"OAuth client credentials not found at {creds_path}.\n"
            "Download them from Google Cloud Console → APIs & Services → "
            "Credentials → OAuth 2.0 Client ID (Desktop app) and save the "
            "JSON there, or update GMAIL_CREDENTIALS_PATH in .env."
        )

    print("Requesting consent for scopes:")
    for s in SCOPES:
        print(f"  • {s}")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(token_path, "w") as f:
        f.write(creds.to_json())

    print(f"\nToken saved to {token_path}")
    print("CareerSarthi can now read Gmail (readonly) and create Calendar reminders.")
    print("Run `careersarthi audit` any time to review what scopes are active.")


if __name__ == "__main__":
    main()
