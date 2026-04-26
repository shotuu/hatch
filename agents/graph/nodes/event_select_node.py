"""Event selection node (Event agent role).

Phase 2: pick top events deterministically from `data/events.json` using the
existing `lib.matching.rank_events` implementation so it stays demo-safe.

Later phases can add an alternate implementation behind an env flag for "live"
event discovery, but the default should remain curated for reliability.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from lib import matching

from ..state import GraphState


def _parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def _window_for_event(event: dict, windows: list[matching.Window]) -> matching.Window:
    start = _parse_iso(event["datetime"])
    end = start + timedelta(minutes=event["duration_minutes"])
    for window in windows:
        if window.start <= start and window.end >= end:
            return window
    return windows[0]


def event_select_node(state: GraphState) -> GraphState:
    if not state.get("ok", True):
        return state

    users = matching.load_users()
    events = matching.load_events()

    raw_windows = state.get("windows")
    window = state.get("window")
    if raw_windows:
        windows = [
            matching.Window(_parse_iso(raw["start"]), _parse_iso(raw["end"]))
            for raw in raw_windows
        ]
    elif window:
        windows = [
            matching.Window(_parse_iso(window["start"]), _parse_iso(window["end"]))
        ]
    else:
        return {**state, "ok": False, "reason": "missing window"}

    ranked = matching.rank_events(events, users, windows)
    if not ranked:
        return {**state, "ok": False, "reason": "no events match"}

    selected_window = _window_for_event(ranked[0], windows)
    return {
        **state,
        "ok": True,
        "window": {
            "start": selected_window.start.isoformat(),
            "end": selected_window.end.isoformat(),
        },
        "ranked": ranked,
        "event": ranked[0],
        "alternates": ranked[1:3],
    }
