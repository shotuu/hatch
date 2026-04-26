"""Availability node (Calendar agent role).

Phase 2 goal: deterministic, demo-safe window selection.
We intentionally do NOT call Google Calendar yet; we reuse the same fallback
logic as `orchestrator.propose_plan_local()`:
  - if OAuth tokens exist for all users, we *can* call freebusy
  - otherwise we treat everyone as free and compute an overlap window

This keeps the LangGraph path compatible with later "LIVE_MODE" phases while
remaining robust for the hackathon demo.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from lib import matching

from ..state import GraphState


def availability_node(state: GraphState) -> GraphState:
    search_hours = int(state.get("search_hours", 168))
    min_window_minutes = int(state.get("min_window_minutes", 120))

    users = matching.load_users()
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(hours=search_hours)

    # Match the existing orchestrator behavior so UI expectations don't change.
    token_paths = {
        u["id"]: u["google_token_path"]
        for u in users
        if (Path(__file__).resolve().parents[3] / u["google_token_path"]).exists()
    }

    allow_mock = os.environ.get("ALLOW_MOCK_CALENDAR", "0") == "1"
    try:
        if len(token_paths) == len(users):
            from lib.integrations import google_calendar

            busy = google_calendar.freebusy(token_paths, now, horizon)
        elif allow_mock:
            busy = {u["id"]: [] for u in users}
        else:
            return {**state, "ok": False, "reason": "missing Google Calendar token"}
    except Exception as e:
        if not allow_mock:
            return {**state, "ok": False, "reason": f"calendar availability failed: {e}"}
        busy = {u["id"]: [] for u in users}

    windows = matching.find_overlap(busy, now, horizon, min_minutes=min_window_minutes)
    if not windows:
        return {**state, "ok": False, "reason": "no shared calendar window found"}

    return {
        **state,
        "ok": True,
        "users": [{"id": u["id"], "name": u["name"]} for u in users],
        "windows": [
            {"start": window.start.isoformat(), "end": window.end.isoformat()}
            for window in windows
        ],
        "window": {"start": windows[0].start.isoformat(), "end": windows[0].end.isoformat()},
    }
