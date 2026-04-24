"""FastAPI bridge between the phone-frame web UI and the agent pipeline.

Run: uvicorn server:app --reload --port 8000
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import orchestrator
from lib import matching

load_dotenv()

app = FastAPI(title="Plans — group chat agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class BookRequest(BaseModel):
    event_id: str


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/users")
def users() -> list[dict]:
    return matching.load_users()


@app.get("/events")
def events() -> list[dict]:
    return matching.load_events()


@app.post("/propose")
def propose() -> dict:
    return orchestrator.propose_plan()


@app.post("/book")
def book(req: BookRequest) -> dict:
    return orchestrator.book_plan(req.event_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host=os.environ.get("SERVER_HOST", "0.0.0.0"),
        port=int(os.environ.get("SERVER_PORT", "8000")),
        reload=True,
    )
