"""Orchestrator — sequential pipeline Calendar → Event → Proposer → (user tap) → Booking.

Two paths:
  • LOCAL  — calls lib.matching + lib.integrations directly. Fast, demo-safe.
  • REMOTE — calls Agentverse-hosted agents over Chat Protocol via AgentClient.

Toggle via env: USE_REMOTE_AGENTS=1

Rule of thumb for the demo: use LOCAL during the live tap-through; record a
separate clip showing REMOTE for the prize narrative.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from lib import matching
from lib.integrations import agentverse
from lib.integrations.agent_client import client
from lib.matching import Window
from lib.protocol import (
    BookingRequest,
    BookingResponse,
    CalendarRequest,
    CalendarResponse,
    EventRequest,
    EventResponse,
    FreeWindow,
    ProposerRequest,
    ProposerResponse,
    RankedEvent,
)

DEMO_TIME_ZONE = ZoneInfo("America/Los_Angeles")


def use_remote() -> bool:
    return os.environ.get("USE_REMOTE_AGENTS", "0") == "1"


# ──────────────────────── LOCAL path ────────────────────────

def _mock_busy(users: list[dict], start: datetime, end: datetime) -> dict:
    return {u["id"]: [] for u in users}


def _allow_mock_calendar() -> bool:
    return os.environ.get("ALLOW_MOCK_CALENDAR", "0") == "1"


def _parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=DEMO_TIME_ZONE)
    return parsed


def _event_bounds(event: dict[str, Any] | RankedEvent) -> tuple[datetime, datetime]:
    if isinstance(event, RankedEvent):
        start = _parse_iso(event.datetime)
        duration_minutes = event.duration_minutes
    else:
        start = _parse_iso(event["datetime"])
        duration_minutes = event["duration_minutes"]
    return start, start + timedelta(minutes=duration_minutes)


def _window_for_event(event: dict[str, Any] | RankedEvent, windows: list[Window]) -> Window:
    start, end = _event_bounds(event)
    for window in windows:
        if window.start <= start and window.end >= end:
            return window
    return windows[0]


def _free_window_for_event(event: RankedEvent, windows: list[FreeWindow]) -> FreeWindow:
    start, end = _event_bounds(event)
    for window in windows:
        if _parse_iso(window.start_iso) <= start and _parse_iso(window.end_iso) >= end:
            return window
    return windows[0]


def _token_paths_for_users(users: list[dict]) -> dict[str, str]:
    return {
        u["id"]: u["google_token_path"]
        for u in users
        if (Path(__file__).parent / u["google_token_path"]).exists()
    }


def _calendar_busy(users: list[dict], start: datetime, end: datetime) -> dict:
    token_paths = _token_paths_for_users(users)
    missing = [u["id"] for u in users if u["id"] not in token_paths]
    if missing:
        if _allow_mock_calendar():
            return _mock_busy(users, start, end)
        raise RuntimeError(f"missing Google Calendar token(s): {', '.join(missing)}")

    from lib.integrations import google_calendar

    return google_calendar.freebusy(token_paths, start, end)


def event_availability(event: dict) -> dict:
    """Return whether every demo member is free for a proposed event."""
    users = matching.load_users()
    start = _parse_iso(event["datetime"])
    end = start + timedelta(minutes=event["duration_minutes"])
    try:
        busy = _calendar_busy(users, start, end)
    except Exception as e:
        return {"ok": False, "available": False, "reason": str(e), "conflicts": []}

    conflicts = []
    for u in users:
        uid = u["id"]
        if any(b_start < end and b_end > start for b_start, b_end in busy.get(uid, [])):
            conflicts.append({"id": uid, "name": u["name"]})
    return {
        "ok": True,
        "available": not conflicts,
        "conflicts": conflicts,
        "start": start.isoformat(),
        "end": end.isoformat(),
    }


def propose_plan_local(*, search_hours: int = 168, min_window_minutes: int = 120) -> dict:
    # LangGraph path is the default since Phase 3 — internal multi-agent
    # orchestration via the nodes in agents/graph/. Set USE_LANGGRAPH=0 to
    # force the legacy direct path (kept around as a demo-safe escape hatch).
    if os.environ.get("USE_LANGGRAPH", "1") == "1":
        from agents.graph.workflow import proposal_graph

        s = proposal_graph().invoke(
            {"search_hours": search_hours, "min_window_minutes": min_window_minutes}
        )
        if not s.get("ok"):
            return {"ok": False, "reason": s.get("reason", "langgraph failed")}
        return {
            "ok": True,
            "window": s["window"],
            "event": s["event"],
            "alternates": s.get("alternates", []),
            "users": s.get("users", []),
            "proposal_text": s.get("proposal_text"),
            "headline": s.get("headline"),
        }

    users = matching.load_users()
    events = matching.load_events()
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(hours=search_hours)

    try:
        busy = _calendar_busy(users, now, horizon)
    except Exception as e:
        return {"ok": False, "reason": f"calendar availability failed: {e}"}
    try:
        busy = _calendar_busy(users, now, horizon)
    except Exception as e:
        return {"ok": False, "reason": f"calendar availability failed: {e}"}

    windows = matching.find_overlap(busy, now, horizon, min_minutes=min_window_minutes)
    if not windows:
        return {"ok": False, "reason": "no shared calendar window found"}
        return {"ok": False, "reason": "no shared calendar window found"}

    ranked = matching.rank_events(events, users, windows)
    if not ranked:
        return {"ok": False, "reason": "no events match"}

    top = ranked[0]
    selected_window = _window_for_event(top, windows)
    return {
        "ok": True,
        "window": {
            "start": selected_window.start.isoformat(),
            "end": selected_window.end.isoformat(),
        },
        "event": top,
        "alternates": ranked[1:3],
        "users": [{"id": u["id"], "name": u["name"]} for u in users],
    }


def book_plan_local(event_id: str) -> dict:
    # LangGraph path is the default since Phase 6 — see agents/graph/workflow.py.
    # The graph resolves event_id from the proposal/panel/events.json (so panel-
    # sourced events like seed_lakers book correctly) and mocks per-user writes
    # when a token is missing (so the demo never visibly fails on a setup gap).
    if os.environ.get("USE_LANGGRAPH", "1") == "1":
        from agents.graph.workflow import booking_graph

        s = booking_graph().invoke({"event_id": event_id})
        return {
            "ok": bool(s.get("ok")),
            "event_id": event_id,
            "calendars_written": int(s.get("calendars_written", 0)),
            "mocked": int(s.get("mocked", 0)),
            "nest_restore": int(s.get("nest_restore", 30)),
            "failures": s.get("failures", []),
            "reason": s.get("reason"),
        }

    events = {e["id"]: e for e in matching.load_events()}
    event = events.get(event_id)
    if not event:
        return {"ok": False, "reason": "unknown event"}

    users = matching.load_users()
    availability = event_availability(event)
    if not availability.get("ok"):
        return {"ok": False, "reason": availability.get("reason", "calendar unavailable")}
    if not availability.get("available"):
        names = ", ".join(c["name"] for c in availability.get("conflicts", []))
        return {"ok": False, "reason": f"calendar conflict for {names}"}

    start = _parse_iso(event["datetime"])
    end = start + timedelta(minutes=event["duration_minutes"])

    written = 0
    failures: list[str] = []
    repo_root = Path(__file__).parent

    try:
        from lib.integrations import google_calendar
    except Exception as e:
        return {"ok": False, "reason": f"google_calendar import: {e}"}

    for u in users:
        token_path = repo_root / u["google_token_path"]
        if not token_path.exists():
            failures.append(f"{u['id']}: no token (run authorize)")
            continue
        try:
            google_calendar.insert_event(
                u["google_token_path"],
                summary=f"Hatch · {event['title']}",
                location=event["location"],
                description=(
                    f"Hatched by your group chat.\n\n{event.get('url', '')}"
                ),
                start=start,
                end=end,
            )
            written += 1
        except Exception as e:
            failures.append(f"{u['id']}: {e}")

    return {
        "ok": written > 0,
        "event_id": event_id,
        "calendars_written": written,
        "nest_restore": 30,
        "failures": failures,
    }


# ──────────────────────── REMOTE path (via AgentClient) ────────────────────────

async def propose_plan_remote(*, search_hours: int = 168, min_window_minutes: int = 120) -> dict:
    users = matching.load_users()
    user_ids = [u["id"] for u in users]
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(hours=search_hours)

    cal: CalendarResponse = await client().request(
        agentverse.CALENDAR,
        CalendarRequest(
            user_ids=user_ids,
            search_start_iso=now.isoformat(),
            search_end_iso=horizon.isoformat(),
            min_window_minutes=min_window_minutes,
        ),
        CalendarResponse,
    )
    if not cal.windows:
        return {"ok": False, "reason": "no shared calendar window found"}
    windows = cal.windows
    if not cal.windows:
        return {"ok": False, "reason": "no shared calendar window found"}
    windows = cal.windows

    ev: EventResponse = await client().request(
        agentverse.EVENT,
        EventRequest(user_ids=user_ids, windows=windows),
        EventResponse,
    )
    if not ev.ranked:
        return {"ok": False, "reason": "no events match"}

    top: RankedEvent = ev.ranked[0]
    selected_window = _free_window_for_event(top, windows)

    prop: ProposerResponse = await client().request(
        agentverse.PROPOSER,
        ProposerRequest(window=selected_window, event=top, user_names=[u["name"] for u in users]),
        ProposerResponse,
    )

    return {
        "ok": True,
        "window": {"start": selected_window.start_iso, "end": selected_window.end_iso},
        "event": top.model_dump(),
        "alternates": [e.model_dump() for e in ev.ranked[1:3]],
        "users": [{"id": u["id"], "name": u["name"]} for u in users],
        "proposal_text": prop.text,
    }


async def book_plan_remote(event_id: str) -> dict:
    users = matching.load_users()
    resp: BookingResponse = await client().request(
        agentverse.BOOKING,
        BookingRequest(event_id=event_id, user_ids=[u["id"] for u in users]),
        BookingResponse,
    )
    return {
        "ok": resp.ok,
        "event_id": event_id,
        "calendars_written": resp.calendars_written,
        "nest_restore": resp.nest_restore,
        "error": resp.error,
    }


# ──────────────────────── Dispatch (used by server.py) ────────────────────────

async def propose_plan() -> dict:
    if use_remote():
        try:
            return await propose_plan_remote()
        except Exception as e:
            # Demo safety: if remote misbehaves mid-pitch, fall back to local.
            print(f"[orchestrator] remote propose failed, falling back: {e}")
    return propose_plan_local()


async def book_plan(event_id: str) -> dict:
    if use_remote():
        try:
            return await book_plan_remote(event_id)
        except Exception as e:
            print(f"[orchestrator] remote book failed, falling back: {e}")
    return book_plan_local(event_id)


# ──────────────────────── Reactive (per-message) ────────────────────────


def react_to_message(text: str, parent_id: str | None = None) -> dict:
    """Run the reactive LangGraph pipeline.

    Pipeline (in agents/graph/workflow.py): trigger → event_synth → format.
    All reactive logic lives inside the nodes; there is no non-graph fallback.

    Returns:
        {
          "should_react": bool,
          "matches": [...],            # event candidates the UI already renders
          "reply": {"headline", "options"},  # UI-stable envelope (Phase 3+)
        }
    """
    try:
        if not should_react_to_message(text):
            return {"should_react": False, "matches": [], "reply": {"headline": "", "options": []}}
        return build_reactive_reply(text, parent_id)
    except Exception as e:
        print(f"[orchestrator] reactive graph failed: {e}")
        return {"should_react": False, "matches": [], "reply": {"headline": "", "options": []}}


def should_react_to_message(text: str) -> bool:
    """Run only the reactive trigger gate."""
    try:
        from agents.graph.nodes.trigger_node import trigger_node

        s = trigger_node({"text": text, "parent_id": ""})
        return bool(s.get("should_react"))
    except Exception as e:
        print(f"[orchestrator] reactive trigger failed: {e}")
        return False


def build_reactive_reply(text: str, parent_id: str | None = None) -> dict:
    """Run the reactive synthesis/format steps after the trigger has fired."""
    try:
        from agents.graph.nodes.event_synth_node import event_synth_node
        from agents.graph.nodes.format_node import format_node

        s = {
            "text": text,
            "parent_id": parent_id or "",
            "should_react": True,
        }
        s = event_synth_node(s)
        s = format_node(s)
        return {
            "should_react": True,
            "matches": s.get("matches") or [],
            "reply": s.get("reply") or {"headline": "", "options": []},
        }
    except Exception as e:
        print(f"[orchestrator] reactive synthesis failed: {e}")
        return {"should_react": False, "matches": [], "reply": {"headline": "", "options": []}}
