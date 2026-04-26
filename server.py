"""FastAPI bridge — thin layer over lib.group_state.

Run: python server.py  (or: uvicorn server:app --reload --port 8000)

Most endpoints mutate the singleton GroupState. Clients GET /state every ~1s.
"""
from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import orchestrator
from lib import matching
from lib.group_state import store

load_dotenv()

app = FastAPI(title="Hatch — group chat agent", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────── request shapes ────────────────────────


class SendMessageRequest(BaseModel):
    user_id: str
    text: str


class ApproveRequest(BaseModel):
    user_id: str


class ProposeIdeaRequest(BaseModel):
    event_id: str
    user_id: str | None = None


class DismissIdeaRequest(BaseModel):
    event_id: str


class HideIdeaRequest(BaseModel):
    event_id: str
    user_id: str


class ReactRequest(BaseModel):
    query: str
    parent_id: str | None = None


class SetWarmthRequest(BaseModel):
    days: int
    auto_propose: bool = True  # when nest goes cold, fire the agent


# ──────────────────────── core ────────────────────────


@app.get("/health")
def health() -> dict:
    return {"ok": True, "use_remote_agents": orchestrator.use_remote()}


@app.get("/state")
def get_state() -> dict:
    return store().snapshot()


@app.post("/reset")
async def reset() -> dict:
    await store().reset()
    return {"ok": True}


# ──────────────────────── chat ────────────────────────


@app.post("/send_message")
async def send_message(req: SendMessageRequest) -> dict:
    if not any(u["id"] == req.user_id for u in matching.load_users()):
        raise HTTPException(400, f"unknown user: {req.user_id}")
    msg = await store().send_message(req.user_id, req.text)

    # Reactive surfacing — runs through the LangGraph reactive pipeline.
    # We persist a bubble whenever the trigger node decided to react, even if
    # event synthesis returned zero matches. That way the user always gets
    # feedback ("Hatch tried but couldn't find anything that fits") instead
    # of silent confusion when an off-LA prompt yields no real venue.
    try:
        should_react = await asyncio.to_thread(orchestrator.should_react_to_message, req.text)
        if not should_react:
            return {"ok": True, "message_id": msg.id, "should_react": False}

        await store().set_hatch_typing(True)
        result = await asyncio.to_thread(orchestrator.build_reactive_reply, req.text, msg.id)
        matches = result.get("matches") or []
        await store().add_reactive(parent_id=msg.id, query=req.text, matches=matches)
        return {"ok": True, "message_id": msg.id, "should_react": True}
    except Exception as e:
        print(f"[reactive] failed: {e}")
        return {"ok": True, "message_id": msg.id, "should_react": False}
    finally:
        await store().set_hatch_typing(False)


@app.post("/react")
async def react(req: ReactRequest) -> dict:
    """Manual reactive trigger (used by 'propose to group' on the panel side)."""
    result = await asyncio.to_thread(orchestrator.react_to_message, req.query, req.parent_id)
    matches = result.get("matches") or []
    if matches:
        await store().add_reactive(parent_id=req.parent_id or "", query=req.query, matches=matches)
    return {"matches": matches, "reply": result.get("reply")}


# ──────────────────────── proposal lifecycle ────────────────────────


@app.post("/propose")
async def propose() -> dict:
    """Run the orchestrator pipeline and stash the proposal in group state."""
    plan = await orchestrator.propose_plan()
    if not plan.get("ok"):
        return plan
    await store().set_proposal(
        window=plan["window"],
        event=plan["event"],
        alternates=plan.get("alternates", []),
    )
    return {"ok": True}


@app.post("/approve")
async def approve(req: ApproveRequest) -> dict:
    s = store()
    p = await s.approve(req.user_id)
    if not p:
        raise HTTPException(400, "no active proposal")

    if s.all_approved():
        # Fire booking
        await s.mark_booking_in_progress()
        result = await orchestrator.book_plan(p.event["id"])
        await s.complete_booking(result)
        return {"ok": True, "approved": True, "all_approved": True, "booking": result}

    return {"ok": True, "approved": True, "all_approved": False}


@app.post("/dismiss_proposal")
async def dismiss_proposal() -> dict:
    await store().skip_proposal()
    return {"ok": True}


@app.post("/set_warmth")
async def set_warmth(req: SetWarmthRequest) -> dict:
    """Dev-console hook: directly set nest warmth (0–30) and, if it just went
    cold and no proposal is active, auto-fire the proactive pipeline so the
    UI shows the agent reacting in real time."""
    s = store()
    new_value = await s.set_warmth(req.days)
    auto_fired = False
    if req.auto_propose and s.is_cold(threshold=3):
        plan = await orchestrator.propose_plan()
        if plan.get("ok"):
            await s.set_proposal(
                window=plan["window"],
                event=plan["event"],
                alternates=plan.get("alternates", []),
            )
            auto_fired = True
    return {"ok": True, "warmth": new_value, "auto_proposed": auto_fired}


@app.post("/swap_alternate")
async def swap_alternate() -> dict:
    p = await store().swap_to_alternate()
    if not p:
        raise HTTPException(400, "no alternates available")
    return {"ok": True}


# ──────────────────────── ideas panel ────────────────────────


@app.post("/dismiss_idea")
async def dismiss_idea(req: DismissIdeaRequest) -> dict:
    """Global removal — used by the booking flow."""
    await store().dismiss_idea(req.event_id)
    return {"ok": True}


@app.post("/hide_idea")
async def hide_idea(req: HideIdeaRequest) -> dict:
    """Per-user Hide — only that viewer stops seeing the idea, and the
    composite ranking score drops by one hide-vote (-10) for everyone else."""
    if not any(u["id"] == req.user_id for u in matching.load_users()):
        raise HTTPException(400, f"unknown user: {req.user_id}")
    await store().hide_idea(req.event_id, req.user_id)
    return {"ok": True}


@app.post("/propose_idea")
async def propose_idea(req: ProposeIdeaRequest) -> dict:
    s = store()
    idea = next((i for i in s.ideas if i.event.get("id") == req.event_id and not i.dismissed), None)
    if idea:
        availability = await asyncio.to_thread(orchestrator.event_availability, idea.event)
        if not availability.get("ok"):
            return {"ok": False, "reason": availability.get("reason", "calendar unavailable")}
        if not availability.get("available"):
            names = ", ".join(c["name"] for c in availability.get("conflicts", []))
            return {"ok": False, "reason": f"calendar conflict for {names}"}

    p = await s.propose_idea(req.event_id, proposer_user_id=req.user_id)
    if not p:
        raise HTTPException(404, "idea not found")
    return {"ok": True}


# ──────────────────────── calendar maintenance ────────────────────────


@app.post("/cleanup")
def cleanup(dry_run: bool = False) -> dict:
    from lib.integrations import google_calendar

    users = matching.load_users()
    summary = []
    total_deleted = 0
    for u in users:
        try:
            items = google_calendar.delete_hatch_events(u["google_token_path"], dry_run=dry_run)
            summary.append({"user": u["id"], "count": len(items)})
            if not dry_run:
                total_deleted += len(items)
        except Exception as e:
            summary.append({"user": u["id"], "error": str(e)})
    return {"ok": True, "dry_run": dry_run, "total_deleted": total_deleted, "per_user": summary}


def _calendar_demo_status() -> dict:
    from lib.integrations import google_calendar

    users = matching.load_users()
    per_user = []
    expected_total = 0
    actual_total = 0
    ready = True
    for u in users:
        token_path = google_calendar.ROOT / u["google_token_path"]
        expected_count = len(google_calendar.demo_busy_fixtures_for(u["id"]))
        expected_total += expected_count
        if not token_path.exists():
            ready = False
            per_user.append({
                "id": u["id"],
                "name": u["name"],
                "ready": False,
                "expected_count": expected_count,
                "actual_count": 0,
                "issues": ["missing Google token"],
            })
            continue
        try:
            status = google_calendar.demo_busy_status(u["google_token_path"], u["id"])
            actual_total += int(status["actual_count"])
            if not status["ready"]:
                ready = False
            per_user.append({"id": u["id"], "name": u["name"], **status})
        except Exception as e:
            ready = False
            per_user.append({
                "id": u["id"],
                "name": u["name"],
                "ready": False,
                "expected_count": expected_count,
                "actual_count": 0,
                "issues": [str(e)],
            })

    return {
        "ok": True,
        "ready": ready and bool(users),
        "expected_total": expected_total,
        "actual_total": actual_total,
        "users": per_user,
    }


@app.get("/calendar_demo/status")
def calendar_demo_status() -> dict:
    return _calendar_demo_status()


@app.post("/calendar_demo/seed")
def seed_calendar_demo() -> dict:
    from lib.integrations import google_calendar

    created_total = 0
    deleted_total = 0
    per_user = []
    for u in matching.load_users():
        token_path = google_calendar.ROOT / u["google_token_path"]
        if not token_path.exists():
            per_user.append({"id": u["id"], "name": u["name"], "error": "missing Google token"})
            continue
        try:
            result = google_calendar.seed_demo_busy_events(u["google_token_path"], u["id"])
            created_total += int(result["created"])
            deleted_total += int(result["deleted"])
            per_user.append({"id": u["id"], "name": u["name"], **result})
        except Exception as e:
            per_user.append({"id": u["id"], "name": u["name"], "error": str(e)})
    return {
        "ok": True,
        "created_total": created_total,
        "deleted_total": deleted_total,
        "per_user": per_user,
        "status": _calendar_demo_status(),
    }


@app.post("/calendar_demo/delete")
def delete_calendar_demo() -> dict:
    from lib.integrations import google_calendar

    deleted_total = 0
    per_user = []
    for u in matching.load_users():
        token_path = google_calendar.ROOT / u["google_token_path"]
        if not token_path.exists():
            per_user.append({"id": u["id"], "name": u["name"], "deleted": 0})
            continue
        try:
            deleted = google_calendar.delete_demo_busy_events(u["google_token_path"])
            deleted_total += len(deleted)
            per_user.append({"id": u["id"], "name": u["name"], "deleted": len(deleted)})
        except Exception as e:
            per_user.append({"id": u["id"], "name": u["name"], "error": str(e)})
    return {
        "ok": True,
        "deleted_total": deleted_total,
        "per_user": per_user,
        "status": _calendar_demo_status(),
    }


@app.get("/users")
def users() -> list[dict]:
    return matching.load_users()


@app.get("/events")
def events() -> list[dict]:
    return matching.load_events()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host=os.environ.get("SERVER_HOST", "0.0.0.0"),
        port=int(os.environ.get("SERVER_PORT", "8005")),
        reload=True,
    )
