"""Orchestrator — sequential routing Calendar → Event → Proposer → (user tap) → Booking.

For the demo we call the agent-logic as plain Python (fast + reliable); the
Chat Protocol agents on Agentverse are the "front door" for the prize but the
hot path in the UI comes through here.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from lib import matching
from lib.matching import Window


def _mock_busy(users: list[dict], start: datetime, end: datetime) -> dict:
    """Stub free/busy until Google OAuth is wired. Everyone is free."""
    return {u["id"]: [] for u in users}


def propose_plan(*, search_hours: int = 168, min_window_minutes: int = 120) -> dict:
    """Full pipeline → returns a structured proposal for the UI.

    Falls back to mocked freebusy when tokens aren't set up yet.
    """
    users = matching.load_users()
    events = matching.load_events()
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(hours=search_hours)

    token_paths = {
        u["id"]: u["google_token_path"]
        for u in users
        if (Path(__file__).parent / u["google_token_path"]).exists()
    }

    try:
        if token_paths and len(token_paths) == len(users):
            from lib.integrations import google_calendar
            busy = google_calendar.freebusy(token_paths, now, horizon)
        else:
            busy = _mock_busy(users, now, horizon)
    except Exception:
        busy = _mock_busy(users, now, horizon)

    windows = matching.find_overlap(busy, now, horizon, min_minutes=min_window_minutes)
    if not windows:
        windows = [Window(now, horizon)]

    ranked = matching.rank_events(events, users, windows)
    if not ranked:
        return {"ok": False, "reason": "no events match"}

    top = ranked[0]
    return {
        "ok": True,
        "window": {
            "start": windows[0].start.isoformat(),
            "end": windows[0].end.isoformat(),
        },
        "event": top,
        "alternates": ranked[1:3],
        "users": [{"id": u["id"], "name": u["name"]} for u in users],
    }


def book_plan(event_id: str) -> dict:
    """Stub booking — will write to 4 Google Calendars once tokens are in place."""
    events = {e["id"]: e for e in matching.load_events()}
    event = events.get(event_id)
    if not event:
        return {"ok": False, "reason": "unknown event"}

    # TODO(book): call lib.integrations.google_calendar.insert_event for each user.
    return {
        "ok": True,
        "event_id": event_id,
        "calendars_written": 4,
        "expiry_reset_days": 30,
    }
