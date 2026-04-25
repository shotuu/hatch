"""Google Calendar — OAuth, freebusy, event insert.

Docs:
  - https://developers.google.com/calendar/api/v3/reference/freebusy/query
  - https://developers.google.com/calendar/api/v3/reference/events/insert

Setup:
  1. Google Cloud Console → OAuth consent screen → External, Testing mode.
     Add all 4 teammates as test users.
  2. Create OAuth client ID (Desktop app is easiest for hackathon).
  3. Fill GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET in .env.
  4. Run `python -m lib.integrations.google_calendar authorize <user_id>`
     once per teammate.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
ROOT = Path(__file__).resolve().parent.parent.parent


def _client_config() -> dict:
    client_id = os.environ["GOOGLE_CLIENT_ID"]
    client_secret = os.environ["GOOGLE_CLIENT_SECRET"]
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def authorize(user_id: str) -> Path:
    """Run OAuth once per user, stash token at data/tokens/<user_id>.json."""
    token_path = ROOT / "data" / "tokens" / f"{user_id}.json"
    token_path.parent.mkdir(parents=True, exist_ok=True)
    flow = InstalledAppFlow.from_client_config(_client_config(), SCOPES)
    creds = flow.run_local_server(port=0)
    token_path.write_text(creds.to_json())
    return token_path


def _credentials(token_path: str) -> Credentials:
    p = ROOT / token_path
    creds = Credentials.from_authorized_user_file(str(p), SCOPES)
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())
        p.write_text(creds.to_json())
    return creds


def _service(token_path: str):
    return build(
        "calendar",
        "v3",
        credentials=_credentials(token_path),
        cache_discovery=False,
    )


def freebusy(
    token_paths_by_user: dict[str, str],
    time_min: datetime,
    time_max: datetime,
) -> dict[str, list[tuple[datetime, datetime]]]:
    out: dict[str, list[tuple[datetime, datetime]]] = {}
    for user_id, token_path in token_paths_by_user.items():
        svc = _service(token_path)
        body = {
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "items": [{"id": "primary"}],
        }
        resp = svc.freebusy().query(body=body).execute()
        busy = resp["calendars"]["primary"].get("busy", [])
        out[user_id] = [
            (datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"]))
            for b in busy
        ]
    return out


def insert_event(
    token_path: str,
    *,
    summary: str,
    location: str,
    description: str,
    start: datetime,
    end: datetime,
) -> dict:
    svc = _service(token_path)
    body = {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": end.isoformat()},
    }
    return svc.events().insert(calendarId="primary", body=body).execute()


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "authorize":
        path = authorize(sys.argv[2])
        print(f"Saved token → {path}")
    else:
        print("usage: python -m lib.integrations.google_calendar authorize <user_id>")
