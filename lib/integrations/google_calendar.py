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


def _dt(value: str) -> datetime:
    """Parse Google/JSON timestamps, including RFC3339 `Z` suffixes."""
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


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
        out[user_id] = [(_dt(b["start"]), _dt(b["end"])) for b in busy]
        out[user_id] = [(_dt(b["start"]), _dt(b["end"])) for b in busy]
    return out


# Marker stamped on every Hatch-created event so cleanup can find them.
HATCH_MARKER_KEY = "source"
HATCH_MARKER_VAL = "hatch"

# Separate marker for demo-only "pre-existing" busy blocks. These are the
# fake-but-plausible calendar events the dev console can seed and remove.
DEMO_BUSY_MARKER_VAL = "hatch-demo-busy"
DEMO_BUSY_SET = "demo-busy-v1"


def _fixture(
    fixture_id: str,
    summary: str,
    start: str,
    end: str,
    *,
    location: str,
) -> dict:
    return {
        "fixture_id": fixture_id,
        "summary": summary,
        "location": location,
        "start": start,
        "end": end,
        "description": "Demo calendar block for Hatch. Safe to delete from the Hatch dev console.",
    }


# Designed to feel like real student calendars while leaving shared open slots
# for Hatch's curated events, especially Sunday late morning.
DEMO_BUSY_FIXTURES: dict[str, list[dict]] = {
    "daniel": [
        _fixture("daniel_01", "CS 188 project sprint", "2026-04-25T17:30:00-07:00", "2026-04-25T21:30:00-07:00", location="Boelter Hall"),
        _fixture("daniel_02", "Late dinner with cousins", "2026-04-25T21:45:00-07:00", "2026-04-25T23:00:00-07:00", location="Sawtelle"),
        _fixture("daniel_03", "Laundry + grocery run", "2026-04-26T08:00:00-07:00", "2026-04-26T09:30:00-07:00", location="Westwood"),
        _fixture("daniel_04", "Study block", "2026-04-26T13:00:00-07:00", "2026-04-26T15:00:00-07:00", location="Powell Library"),
        _fixture("daniel_05", "Family FaceTime", "2026-04-26T18:00:00-07:00", "2026-04-26T19:30:00-07:00", location="Home"),
    ],
    "jono": [
        _fixture("jono_01", "Pickup basketball", "2026-04-25T17:45:00-07:00", "2026-04-25T20:15:00-07:00", location="John Wooden Center"),
        _fixture("jono_02", "Birthday drinks for Nate", "2026-04-25T20:30:00-07:00", "2026-04-25T23:30:00-07:00", location="Koreatown"),
        _fixture("jono_03", "Morning run", "2026-04-26T07:30:00-07:00", "2026-04-26T09:15:00-07:00", location="Veteran Ave"),
        _fixture("jono_04", "Shift at lab", "2026-04-26T13:30:00-07:00", "2026-04-26T16:30:00-07:00", location="Engineering VI"),
        _fixture("jono_05", "Comedy workshop", "2026-04-26T20:00:00-07:00", "2026-04-26T22:30:00-07:00", location="West Hollywood"),
    ],
    "andrew": [
        _fixture("andrew_01", "Studio critique prep", "2026-04-25T16:30:00-07:00", "2026-04-25T19:30:00-07:00", location="Broad Art Center"),
        _fixture("andrew_02", "Movie night", "2026-04-25T20:00:00-07:00", "2026-04-25T22:30:00-07:00", location="AMC Century City"),
        _fixture("andrew_03", "Yoga class", "2026-04-26T08:00:00-07:00", "2026-04-26T09:30:00-07:00", location="Culver City"),
        _fixture("andrew_04", "Lab check-in", "2026-04-26T12:30:00-07:00", "2026-04-26T14:30:00-07:00", location="UCLA CNSI"),
        _fixture("andrew_05", "Family dinner", "2026-04-26T18:30:00-07:00", "2026-04-26T20:00:00-07:00", location="Pasadena"),
    ],
}

DEFAULT_DEMO_BUSY_FIXTURES = [
    _fixture("default_01", "Section meeting", "2026-04-25T17:00:00-07:00", "2026-04-25T20:00:00-07:00", location="UCLA"),
    _fixture("default_02", "Roommate dinner", "2026-04-25T20:15:00-07:00", "2026-04-25T22:00:00-07:00", location="Westwood"),
    _fixture("default_03", "Gym", "2026-04-26T08:00:00-07:00", "2026-04-26T09:15:00-07:00", location="John Wooden Center"),
    _fixture("default_04", "Club prep", "2026-04-26T12:45:00-07:00", "2026-04-26T14:45:00-07:00", location="Kerckhoff Hall"),
    _fixture("default_05", "Call home", "2026-04-26T18:00:00-07:00", "2026-04-26T19:30:00-07:00", location="Home"),
]


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


def _demo_busy_body(user_id: str, fixture: dict, index: int) -> dict:
    return {
        "summary": fixture["summary"],
        "location": fixture["location"],
        "description": fixture["description"],
        "start": {"dateTime": fixture["start"]},
        "end": {"dateTime": fixture["end"]},
        "extendedProperties": {
            "private": {
                HATCH_MARKER_KEY: DEMO_BUSY_MARKER_VAL,
                "fixture_set": DEMO_BUSY_SET,
                "fixture_user": user_id,
                "fixture_id": fixture["fixture_id"],
                "fixture_index": str(index),
            },
        },
    }


def demo_busy_fixtures_for(user_id: str) -> list[dict]:
    """Expected busy blocks for a demo user, in canonical insertion order."""
    if user_id in DEMO_BUSY_FIXTURES:
        return DEMO_BUSY_FIXTURES[user_id]
    return [
        {**fixture, "fixture_id": f"{user_id}_{index + 1:02}"}
        for index, fixture in enumerate(DEFAULT_DEMO_BUSY_FIXTURES)
    ]


def list_demo_busy_events(token_path: str) -> list[dict]:
    svc = _service(token_path)
    resp = svc.events().list(
        calendarId="primary",
        privateExtendedProperty=f"{HATCH_MARKER_KEY}={DEMO_BUSY_MARKER_VAL}",
        singleEvents=True,
        orderBy="startTime",
        maxResults=2500,
    ).execute()
    return resp.get("items", [])


def _event_matches_fixture(ev: dict, user_id: str, fixture: dict, index: int) -> bool:
    private = ev.get("extendedProperties", {}).get("private", {})
    start = ev.get("start", {}).get("dateTime")
    end = ev.get("end", {}).get("dateTime")
    if not start or not end:
        return False
    return (
        ev.get("summary") == fixture["summary"]
        and ev.get("location", "") == fixture["location"]
        and ev.get("description", "") == fixture["description"]
        and _dt(start).isoformat() == _dt(fixture["start"]).isoformat()
        and _dt(end).isoformat() == _dt(fixture["end"]).isoformat()
        and private.get(HATCH_MARKER_KEY) == DEMO_BUSY_MARKER_VAL
        and private.get("fixture_set") == DEMO_BUSY_SET
        and private.get("fixture_user") == user_id
        and private.get("fixture_id") == fixture["fixture_id"]
        and private.get("fixture_index") == str(index)
    )


def demo_busy_status(token_path: str, user_id: str) -> dict:
    expected = demo_busy_fixtures_for(user_id)
    actual = list_demo_busy_events(token_path)
    issues: list[str] = []

    if len(actual) != len(expected):
        issues.append(f"expected {len(expected)} events, found {len(actual)}")

    for index, fixture in enumerate(expected):
        if index >= len(actual):
            issues.append(f"missing #{index + 1}: {fixture['summary']}")
            continue
        if not _event_matches_fixture(actual[index], user_id, fixture, index):
            got = actual[index].get("summary", "(untitled)")
            issues.append(
                f"#{index + 1} changed or out of order: "
                f"expected {fixture['summary']}, found {got}"
            )

    if len(actual) > len(expected):
        for ev in actual[len(expected):]:
            issues.append(f"extra tagged event: {ev.get('summary', '(untitled)')}")

    return {
        "ready": not issues,
        "expected_count": len(expected),
        "actual_count": len(actual),
        "issues": issues,
    }


def seed_demo_busy_events(token_path: str, user_id: str) -> dict:
    """Reset this user's demo busy blocks to the canonical order."""
    deleted = delete_demo_busy_events(token_path)
    created = []
    svc = _service(token_path)
    for index, fixture in enumerate(demo_busy_fixtures_for(user_id)):
        created.append(
            svc.events()
            .insert(calendarId="primary", body=_demo_busy_body(user_id, fixture, index))
            .execute()
        )
    return {
        "deleted": len(deleted),
        "created": len(created),
        "status": demo_busy_status(token_path, user_id),
    }


def delete_demo_busy_events(token_path: str) -> list[dict]:
    items = list_demo_busy_events(token_path)
    for ev in items:
        try:
            delete_event(token_path, ev["id"])
        except Exception as e:
            print(f"  ! failed to delete demo busy event {ev.get('summary')}: {e}")
    return items


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
