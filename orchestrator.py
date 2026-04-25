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


def use_remote() -> bool:
    return os.environ.get("USE_REMOTE_AGENTS", "0") == "1"


# ──────────────────────── LOCAL path ────────────────────────

def _mock_busy(users: list[dict], start: datetime, end: datetime) -> dict:
    return {u["id"]: [] for u in users}


def propose_plan_local(*, search_hours: int = 168, min_window_minutes: int = 120) -> dict:
    # Optional LangGraph path (internal multi-agent orchestration).
    # This keeps the public FastAPI/UI contract identical, while letting you
    # truthfully say the pipeline is orchestrated via LangGraph.
    if os.environ.get("USE_LANGGRAPH", "0") == "1":
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
        }

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
        "window": {"start": windows[0].start.isoformat(), "end": windows[0].end.isoformat()},
        "event": top,
        "alternates": ranked[1:3],
        "users": [{"id": u["id"], "name": u["name"]} for u in users],
    }


def book_plan_local(event_id: str) -> dict:
    events = {e["id"]: e for e in matching.load_events()}
    event = events.get(event_id)
    if not event:
        return {"ok": False, "reason": "unknown event"}

    users = matching.load_users()
    start = datetime.fromisoformat(event["datetime"])
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
        "expiry_reset_days": 30,
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
    windows = cal.windows or [FreeWindow(start_iso=now.isoformat(), end_iso=horizon.isoformat())]

    ev: EventResponse = await client().request(
        agentverse.EVENT,
        EventRequest(user_ids=user_ids, windows=windows),
        EventResponse,
    )
    if not ev.ranked:
        return {"ok": False, "reason": "no events match"}

    top: RankedEvent = ev.ranked[0]

    prop: ProposerResponse = await client().request(
        agentverse.PROPOSER,
        ProposerRequest(window=windows[0], event=top, user_names=[u["name"] for u in users]),
        ProposerResponse,
    )

    return {
        "ok": True,
        "window": {"start": windows[0].start_iso, "end": windows[0].end_iso},
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
        "expiry_reset_days": resp.expiry_reset_days,
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
    from agents.graph.workflow import reactive_graph

    try:
        s = reactive_graph().invoke({"text": text, "parent_id": parent_id or ""})
        return {
            "should_react": bool(s.get("should_react")),
            "matches": s.get("matches") or [],
            "reply": s.get("reply") or {"headline": "", "options": []},
        }
    except Exception as e:
        print(f"[orchestrator] reactive graph failed: {e}")
        return {"should_react": False, "matches": [], "reply": {"headline": "", "options": []}}
