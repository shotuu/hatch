"""Eligibility node for the booking workflow (Phase 6).

Resolves an `event_id` to a real event dict and pulls the group member list,
so `calendar_writer_node` can do its job without re-doing lookups. Fails fast
with a structured `reason` if anything's off — booking should never reach the
calendar-write step on partial state.

Why we look in three places:
  1. The current proposal's `event` — most authoritative; it's the exact dict
     the user just approved, including any panel-sourced events (seed_lakers,
     reactive synthesis hits) that aren't in the curated `events.json`.
  2. The live ideas panel — fallback if there's no current proposal but the
     event_id matches something we've surfaced.
  3. `events.json` — the curated catalogue. Last resort.

Without (1) and (2), booking a Phase 5 panel-sourced event (Lakers, LACMA,
Smorgasburg, anything from reactive synthesis) would fail with "unknown event"
because none of those live in `events.json`. This node is what makes Phase 5
+ Phase 6 actually compose.
"""

from __future__ import annotations

from ..state import BookingState


def _resolve_event(event_id: str) -> dict | None:
    if not event_id:
        return None

    try:
        from lib.group_state import store

        s = store()
        p = s.current_proposal
        if p and (p.event or {}).get("id") == event_id:
            return p.event

        for idea in s.ideas:
            if (idea.event or {}).get("id") == event_id:
                return idea.event
    except Exception:
        pass

    try:
        from lib import matching

        for e in matching.load_events():
            if e.get("id") == event_id:
                return e
    except Exception:
        pass

    return None


def eligibility_node(state: BookingState) -> BookingState:
    event_id = state.get("event_id") or ""
    if not event_id:
        return {**state, "ok": False, "reason": "missing event_id"}

    event = _resolve_event(event_id)
    if not event:
        return {**state, "ok": False, "reason": f"unknown event: {event_id}"}

    if not event.get("datetime") or not event.get("duration_minutes"):
        return {
            **state,
            "ok": False,
            "reason": "event missing datetime or duration_minutes",
        }

    try:
        from lib import matching

        users = matching.load_users()
    except Exception as e:
        return {**state, "ok": False, "reason": f"load_users failed: {e}"}

    if not users:
        return {**state, "ok": False, "reason": "no users configured"}

    return {**state, "ok": True, "event": event, "users": users}
