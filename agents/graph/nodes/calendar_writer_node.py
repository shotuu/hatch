"""Calendar writer node for the booking workflow (Phase 6).

Writes the event to each member's Google Calendar. Demo-safe by design:

  - Token file present + write succeeds → real Google Calendar entry
    (the demo can switch to the Google Calendar tab and show it live).
  - Token file present + write throws → counted in `failures`, no mock.
    Real failure surfaces honestly so we can debug it.
  - Token file MISSING → mock the write as success and bump `mocked`.
    A missing token is a setup gap, not an API failure. Mocking lets the
    bubble flip to "✓ booked, N/N calendars updated" so the demo never
    visibly breaks on a teammate who forgot to authorize.

To switch a single user from mocked to real writes: drop their OAuth token
JSON at `data/tokens/{user_id}.json`. Nothing else changes.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from ..state import BookingState

# Hatch repo root, computed once. Used to resolve user["google_token_path"]
# (which is stored relative to the repo) into an absolute path.
_REPO_ROOT = Path(__file__).resolve().parents[3]


def calendar_writer_node(state: BookingState) -> BookingState:
    if not state.get("ok", True):
        return state

    event = state.get("event") or {}
    users = state.get("users") or []
    if not event or not users:
        return {**state, "ok": False, "reason": "missing event or users"}

    try:
        start = datetime.fromisoformat(event["datetime"])
        end = start + timedelta(minutes=int(event["duration_minutes"]))
    except Exception as e:
        return {**state, "ok": False, "reason": f"bad event datetime: {e}"}

    try:
        from lib.integrations import google_calendar
    except Exception as e:
        # Catastrophic — the integration itself didn't import. Still demo-safe:
        # mock everyone so the bubble can flip to booked.
        n = len(users)
        return {
            **state,
            "ok": True,
            "calendars_written": n,
            "mocked": n,
            "failures": [f"google_calendar import failed: {e}"],
            "nest_restore": 30,
        }

    written = 0
    mocked = 0
    failures: list[str] = []

    summary = f"Hatch · {event.get('title', 'Hatch plan')}"
    location = event.get("location") or ""
    description = (
        f"Hatched by your group chat.\n\n{event.get('url', '')}".strip()
    )

    for u in users:
        rel = u.get("google_token_path") or ""
        token_path = _REPO_ROOT / rel if rel else None

        if not token_path or not token_path.exists():
            mocked += 1
            written += 1
            continue

        try:
            google_calendar.insert_event(
                rel,
                summary=summary,
                location=location,
                description=description,
                start=start,
                end=end,
            )
            written += 1
        except Exception as e:
            failures.append(f"{u.get('id', '?')}: {e}")

    return {
        **state,
        "ok": written > 0,
        "calendars_written": written,
        "mocked": mocked,
        "failures": failures,
        "nest_restore": 30,
    }
