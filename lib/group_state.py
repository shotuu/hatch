"""Singleton in-memory group state — shared across all phone viewers.

Every viewer (each phone instance in the demo) polls /state and renders the
same snapshot. Mutations (send message, approve, swap alternate, dismiss idea,
wipe) happen via the dedicated endpoints in server.py.

For a hackathon demo this is fine; restart server.py = clean slate.
"""
from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from lib import matching


# ──────────────────────── data shapes ────────────────────────


@dataclass
class ChatMessage:
    id: str
    kind: Literal["user", "reactive"]
    ts: str
    # user fields
    author_id: str | None = None
    text: str | None = None
    # reactive fields
    parent_id: str | None = None
    query: str | None = None
    matches: list[dict] = field(default_factory=list)


ProposalStatus = Literal["pending", "booking", "booked", "skipped"]


@dataclass
class Proposal:
    id: str
    window: dict
    event: dict
    alternates: list[dict]
    approvals: dict[str, bool]  # user_id → approved?
    status: ProposalStatus = "pending"
    created_at: str = ""
    booking: dict | None = None  # set after booking attempt


@dataclass
class Idea:
    event: dict
    source: Literal["reactive", "proposal", "alternate"]
    score: int
    seen_at: str
    dismissed: bool = False


# ──────────────────────── store ────────────────────────


class GroupState:
    def __init__(self) -> None:
        self.lock = asyncio.Lock()
        self.messages: list[ChatMessage] = []
        self.current_proposal: Proposal | None = None
        self.expiry_days: int = 6
        self.last_booking: dict | None = None
        self.ideas: list[Idea] = []  # ordered by score desc

    # ─── snapshot ───

    def snapshot(self) -> dict:
        return {
            "messages": [asdict(m) for m in self.messages],
            "current_proposal": asdict(self.current_proposal) if self.current_proposal else None,
            "expiry_days": self.expiry_days,
            "last_booking": self.last_booking,
            "ideas": [asdict(i) for i in self.ideas if not i.dismissed],
            "users": [{"id": u["id"], "name": u["name"], "color": u["avatar_color"]} for u in matching.load_users()],
        }

    # ─── helpers ───

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _user_ids(self) -> list[str]:
        return [u["id"] for u in matching.load_users()]

    def _add_idea(self, event: dict, source: str, score: int = 0) -> None:
        # de-dupe on event id
        for i in self.ideas:
            if i.event.get("id") == event.get("id"):
                i.dismissed = False
                if score > i.score:
                    i.score = score
                return
        self.ideas.append(Idea(event=event, source=source, score=score, seen_at=self._now_iso()))
        self.ideas.sort(key=lambda i: -i.score)

    # ─── mutations ───

    async def send_message(self, author_id: str, text: str) -> ChatMessage:
        async with self.lock:
            msg = ChatMessage(
                id=f"m_{uuid4().hex[:8]}",
                kind="user",
                ts=self._now_iso(),
                author_id=author_id,
                text=text,
            )
            self.messages.append(msg)
            return msg

    async def add_reactive(self, parent_id: str, query: str, matches: list[dict]) -> ChatMessage:
        async with self.lock:
            msg = ChatMessage(
                id=f"r_{uuid4().hex[:8]}",
                kind="reactive",
                ts=self._now_iso(),
                parent_id=parent_id,
                query=query,
                matches=matches,
            )
            self.messages.append(msg)
            for e in matches:
                self._add_idea(e, source="reactive", score=int(e.get("_score", 0)) or 1)
            return msg

    async def set_proposal(self, *, window: dict, event: dict, alternates: list[dict]) -> Proposal:
        async with self.lock:
            user_ids = self._user_ids()
            self.current_proposal = Proposal(
                id=f"p_{uuid4().hex[:8]}",
                window=window,
                event=event,
                alternates=alternates,
                approvals={uid: False for uid in user_ids},
                status="pending",
                created_at=self._now_iso(),
            )
            self._add_idea(event, source="proposal", score=int(event.get("_score", 0)) or 5)
            for alt in alternates:
                self._add_idea(alt, source="alternate", score=int(alt.get("_score", 0)) or 2)
            return self.current_proposal

    async def approve(self, user_id: str) -> Proposal | None:
        async with self.lock:
            p = self.current_proposal
            if not p or p.status != "pending":
                return p
            if user_id not in p.approvals:
                return p
            p.approvals[user_id] = True
            return p

    def all_approved(self) -> bool:
        p = self.current_proposal
        return bool(p and p.status == "pending" and all(p.approvals.values()))

    async def mark_booking_in_progress(self) -> None:
        async with self.lock:
            if self.current_proposal:
                self.current_proposal.status = "booking"

    async def complete_booking(self, result: dict) -> None:
        async with self.lock:
            if self.current_proposal:
                self.current_proposal.status = "booked"
                self.current_proposal.booking = result
            self.last_booking = result
            self.expiry_days = 30  # reset

    async def skip_proposal(self) -> None:
        async with self.lock:
            if self.current_proposal:
                self.current_proposal.status = "skipped"
                self.current_proposal = None

    async def swap_to_alternate(self, alt_index: int = 0) -> Proposal | None:
        async with self.lock:
            p = self.current_proposal
            if not p or not p.alternates or alt_index >= len(p.alternates):
                return p
            new_event = p.alternates.pop(alt_index)
            p.alternates.append(p.event)
            p.event = new_event
            p.approvals = {uid: False for uid in p.approvals}
            self._add_idea(new_event, source="proposal", score=int(new_event.get("_score", 0)) or 5)
            return p

    async def dismiss_idea(self, event_id: str) -> None:
        async with self.lock:
            for i in self.ideas:
                if i.event.get("id") == event_id:
                    i.dismissed = True

    async def propose_idea(self, event_id: str) -> Proposal | None:
        """Take an idea from the panel and turn it into the current proposal."""
        from datetime import timedelta

        async with self.lock:
            idea = next((i for i in self.ideas if i.event.get("id") == event_id), None)
            if not idea:
                return None
            event = idea.event
            start = datetime.fromisoformat(event["datetime"])
            end = start + timedelta(minutes=event["duration_minutes"])
            user_ids = self._user_ids()
            self.current_proposal = Proposal(
                id=f"p_{uuid4().hex[:8]}",
                window={"start": start.isoformat(), "end": end.isoformat()},
                event=event,
                alternates=[],
                approvals={uid: False for uid in user_ids},
                status="pending",
                created_at=self._now_iso(),
            )
            return self.current_proposal

    async def set_warmth(self, days: int) -> int:
        """Directly set the nest-warmth value (0–30). Used by dev time controls."""
        async with self.lock:
            self.expiry_days = max(0, min(30, int(days)))
            return self.expiry_days

    def is_cold(self, threshold: int = 3) -> bool:
        return self.expiry_days <= threshold and self.current_proposal is None

    async def reset(self) -> None:
        async with self.lock:
            self.messages = _seed_messages()
            self.current_proposal = None
            self.expiry_days = 6
            self.last_booking = None
            self.ideas = []


# ──────────────────────── singleton + seed data ────────────────────────


def _seed_messages() -> list[ChatMessage]:
    """Initial dead-chat state for the demo."""
    return [
        ChatMessage(id="m_seed1", kind="user", ts="3 weeks ago", author_id="jono", text="miss y'all 😭"),
        ChatMessage(id="m_seed2", kind="user", ts="3 weeks ago", author_id="andrew", text="we gotta do something soon fr"),
        ChatMessage(id="m_seed3", kind="user", ts="2 weeks ago", author_id="jono", text="down whenever, lmk"),
    ]


_state: GroupState | None = None


def store() -> GroupState:
    global _state
    if _state is None:
        _state = GroupState()
        _state.messages = _seed_messages()
    return _state
