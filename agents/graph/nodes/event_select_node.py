"""Event selection node (Event agent role).

Phase 5 — Source of truth for the proactive event:
  1. Prefer the top non-dismissed idea already living in the panel. The panel
     reflects everything the agent has surfaced so far (seeded popular spots,
     reactive matches from real chat messages, anything the user has voted on)
     ranked by `ranking_node`'s composite score. Reusing it means the proactive
     proposal feels coherent with what users have actually been seeing.
  2. Fall back to `data/events.json` filtered against the availability window
     so the demo is never empty-handed even if the panel got fully wiped.

When using a panel idea, the window is rebuilt from the idea's own
`datetime` + `duration_minutes` so the proposal bubble's "you're free X to Y"
line matches the event's actual time slot. (The mock free/busy treats everyone
as free, so this is correct under the hackathon's demo conditions.)
"""

from __future__ import annotations

from datetime import datetime, timedelta

from lib import matching

from ..state import GraphState


def _top_panel_idea() -> dict | None:
    """Return the top-ranked, non-dismissed event from the live panel, or None.

    `store().ideas` is already sorted by `ranking_node` (composite score: votes,
    hides, recency, base score). We just take the first non-dismissed one. We
    don't filter on per-user `hidden` because the proactive proposal is shown
    to the whole group, not a single viewer.
    """
    try:
        from lib.group_state import store

        for idea in store().ideas:
            if idea.dismissed:
                continue
            ev = idea.event or {}
            if not ev.get("datetime") or not ev.get("title"):
                continue
            return ev
        return None
    except Exception:
        return None


def _window_from_event(ev: dict) -> dict | None:
    """Derive a window dict from an event's datetime + duration."""
    try:
        start = datetime.fromisoformat(ev["datetime"])
        duration = int(ev.get("duration_minutes") or 120)
        end = start + timedelta(minutes=duration)
        return {"start": start.isoformat(), "end": end.isoformat()}
    except Exception:
        return None


def event_select_node(state: GraphState) -> GraphState:
    if not state.get("ok", True):
        return state

    panel_event = _top_panel_idea()
    if panel_event is not None:
        window = _window_from_event(panel_event) or state.get("window")
        if window is None:
            return {**state, "ok": False, "reason": "panel idea missing datetime"}
        return {
            **state,
            "ok": True,
            "ranked": [panel_event],
            "event": panel_event,
            "alternates": [],
            "window": window,
        }

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
