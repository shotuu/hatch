"""FastAPI bridge between the phone-frame web UI and the agent pipeline.

Run: uvicorn server:app --reload --port 8000
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import orchestrator
from lib import matching

load_dotenv()

app = FastAPI(title="Hatch — group chat agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class BookRequest(BaseModel):
    event_id: str


class ReactRequest(BaseModel):
    query: str


@app.get("/health")
def health() -> dict:
    return {"ok": True, "use_remote_agents": orchestrator.use_remote()}


@app.get("/users")
def users() -> list[dict]:
    return matching.load_users()


@app.get("/events")
def events() -> list[dict]:
    return matching.load_events()


@app.post("/propose")
async def propose() -> dict:
    return await orchestrator.propose_plan()


@app.post("/book")
async def book(req: BookRequest) -> dict:
    return await orchestrator.book_plan(req.event_id)


@app.post("/react")
def react(req: ReactRequest) -> dict:
    """Reactive mode — match a free-text query against curated events."""
    q = req.query.lower().strip()
    if not q:
        return {"matches": []}
    terms = [t for t in q.split() if len(t) > 2]
    matches = []
    for e in matching.load_events():
        haystack = f"{e['title']} {' '.join(e['tags'])}".lower()
        if any(t in haystack for t in terms):
            matches.append(e)
    return {"matches": matches[:3]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host=os.environ.get("SERVER_HOST", "0.0.0.0"),
        port=int(os.environ.get("SERVER_PORT", "8000")),
        reload=True,
    )
