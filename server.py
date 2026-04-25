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
from lib import event_synthesis, matching
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


class DismissIdeaRequest(BaseModel):
    event_id: str


class ReactRequest(BaseModel):
    query: str
    parent_id: str | None = None


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

    # Reactive surfacing — AI synthesis gates itself on activity intent.
    try:
        matches = await asyncio.to_thread(event_synthesis.find_reactive_matches, req.text)
        if matches:
            await store().add_reactive(parent_id=msg.id, query=req.text, matches=matches)
    except Exception as e:
        print(f"[reactive] failed: {e}")

    return {"ok": True, "message_id": msg.id}


@app.post("/react")
async def react(req: ReactRequest) -> dict:
    """Manual reactive trigger (used by 'propose to group' on the panel side)."""
    matches = await asyncio.to_thread(event_synthesis.find_reactive_matches, req.query)
    if matches:
        await store().add_reactive(parent_id=req.parent_id or "", query=req.query, matches=matches)
    return {"matches": matches}


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


@app.post("/swap_alternate")
async def swap_alternate() -> dict:
    p = await store().swap_to_alternate()
    if not p:
        raise HTTPException(400, "no alternates available")
    return {"ok": True}


# ──────────────────────── ideas panel ────────────────────────


@app.post("/dismiss_idea")
async def dismiss_idea(req: DismissIdeaRequest) -> dict:
    await store().dismiss_idea(req.event_id)
    return {"ok": True}


@app.post("/propose_idea")
async def propose_idea(req: ProposeIdeaRequest) -> dict:
    p = await store().propose_idea(req.event_id)
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
        port=int(os.environ.get("SERVER_PORT", "8000")),
        reload=True,
    )
