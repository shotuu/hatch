"""Typed payload schemas for agent-to-agent messages.

Chat Protocol carries `TextContent` (strings). To pass structured data we
JSON-encode these Pydantic models into the text body. The agents and the
orchestrator both import from here so the contract is single-sourced.

Convention: every payload has a `type` discriminator. If you ever consolidate
into one agent, the discriminator lets you route by type.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


# ──────────────────────── Calendar agent ────────────────────────

class FreeWindow(BaseModel):
    start_iso: str
    end_iso: str


class CalendarRequest(BaseModel):
    type: Literal["calendar_request"] = "calendar_request"
    user_ids: list[str]
    search_start_iso: str
    search_end_iso: str
    min_window_minutes: int = 120


class CalendarResponse(BaseModel):
    type: Literal["calendar_response"] = "calendar_response"
    windows: list[FreeWindow]


# ──────────────────────── Event agent ────────────────────────

class RankedEvent(BaseModel):
    id: str
    title: str
    datetime: str
    duration_minutes: int
    location: str
    price: float
    url: str
    tags: list[str]
    score: int


class EventRequest(BaseModel):
    type: Literal["event_request"] = "event_request"
    user_ids: list[str]
    windows: list[FreeWindow]


class EventResponse(BaseModel):
    type: Literal["event_response"] = "event_response"
    ranked: list[RankedEvent]


# ──────────────────────── Proposer agent ────────────────────────

class ProposerRequest(BaseModel):
    type: Literal["proposer_request"] = "proposer_request"
    window: FreeWindow
    event: RankedEvent
    user_names: list[str]


class ProposerResponse(BaseModel):
    type: Literal["proposer_response"] = "proposer_response"
    text: str


# ──────────────────────── Booking agent ────────────────────────

class BookingRequest(BaseModel):
    type: Literal["booking_request"] = "booking_request"
    event_id: str
    user_ids: list[str]


class BookingResponse(BaseModel):
    type: Literal["booking_response"] = "booking_response"
    ok: bool
    calendars_written: int = 0
    expiry_reset_days: int = 30
    error: str | None = None
