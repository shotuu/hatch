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

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

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


# Marker stamped on every Hatch-created event so cleanup can find them.
HATCH_MARKER_KEY = "source"
HATCH_MARKER_VAL = "hatch"


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
        "extendedProperties": {
            "private": {HATCH_MARKER_KEY: HATCH_MARKER_VAL},
        },
    }
    return svc.events().insert(calendarId="primary", body=body).execute()


def list_hatch_events(
    token_path: str,
    *,
    time_min: datetime | None = None,
    time_max: datetime | None = None,
) -> list[dict]:
    """Return every Hatch-tagged event in the window. Defaults to ± 60 days from now."""
    svc = _service(token_path)
    now = datetime.now().astimezone()
    if time_min is None:
        time_min = now.replace(microsecond=0) - _days(60)
    if time_max is None:
        time_max = now.replace(microsecond=0) + _days(60)
    resp = svc.events().list(
        calendarId="primary",
        privateExtendedProperty=f"{HATCH_MARKER_KEY}={HATCH_MARKER_VAL}",
        timeMin=time_min.isoformat(),
        timeMax=time_max.isoformat(),
        singleEvents=True,
        maxResults=2500,
    ).execute()
    return resp.get("items", [])


def delete_event(token_path: str, event_id: str) -> None:
    svc = _service(token_path)
    svc.events().delete(calendarId="primary", eventId=event_id).execute()


def delete_hatch_events(
    token_path: str,
    *,
    time_min: datetime | None = None,
    time_max: datetime | None = None,
    dry_run: bool = False,
) -> list[dict]:
    """Delete every Hatch-tagged event in the window. Returns what was (or would be) deleted."""
    items = list_hatch_events(token_path, time_min=time_min, time_max=time_max)
    if not dry_run:
        for ev in items:
            try:
                delete_event(token_path, ev["id"])
            except Exception as e:
                print(f"  ! failed to delete {ev.get('summary')}: {e}")
    return items


def _days(n: int):
    from datetime import timedelta
    return timedelta(days=n)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "authorize":
        path = authorize(sys.argv[2])
        print(f"Saved token → {path}")
    elif len(sys.argv) >= 3 and sys.argv[1] == "cleanup":
        user_id = sys.argv[2]
        token = ROOT / "data" / "tokens" / f"{user_id}.json"
        deleted = delete_hatch_events(str(token.relative_to(ROOT)))
        print(f"Deleted {len(deleted)} Hatch event(s) for {user_id}")
    else:
        print(
            "usage:\n"
            "  python -m lib.integrations.google_calendar authorize <user_id>\n"
            "  python -m lib.integrations.google_calendar cleanup   <user_id>"
        )
