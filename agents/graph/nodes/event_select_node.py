"""Event selection node (Event agent role).

Phase 2: pick top events deterministically from `data/events.json` using the
existing `lib.matching.rank_events` implementation so it stays demo-safe.

Later phases can add an alternate implementation behind an env flag for "live"
event discovery, but the default should remain curated for reliability.
"""

from __future__ import annotations

from datetime import datetime

from lib import matching

from ..state import GraphState


def event_select_node(state: GraphState) -> GraphState:
    if not state.get("ok", True):
        return state

    users = matching.load_users()
    events = matching.load_events()

    window = state.get("window")
    if not window:
        return {**state, "ok": False, "reason": "missing window"}

    start = datetime.fromisoformat(window["start"])
    end = datetime.fromisoformat(window["end"])
    windows = [matching.Window(start, end)]

    ranked = matching.rank_events(events, users, windows)
    if not ranked:
        return {**state, "ok": False, "reason": "no events match"}

    return {
        **state,
        "ok": True,
        "ranked": ranked,
        "event": ranked[0],
        "alternates": ranked[1:3],
    }

