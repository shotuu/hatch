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
        if (Path(__file__).resolve().parents[2] / u["google_token_path"]).exists()
    }

    try:
        if token_paths and len(token_paths) == len(users):
            from lib.integrations import google_calendar

            busy = google_calendar.freebusy(token_paths, now, horizon)
        else:
            busy = {u["id"]: [] for u in users}
    except Exception:
        busy = {u["id"]: [] for u in users}

    windows = matching.find_overlap(busy, now, horizon, min_minutes=min_window_minutes)
    if not windows:
        windows = [matching.Window(now, horizon)]

    return {
        **state,
        "ok": True,
        "users": [{"id": u["id"], "name": u["name"]} for u in users],
        "window": {"start": windows[0].start.isoformat(), "end": windows[0].end.isoformat()},
    }

