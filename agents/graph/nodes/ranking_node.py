"""Ranking node — composite scoring + dedupe for the ideas panel.

No LLM. Pure mechanic. Lives as a LangGraph node (not a util) so the
orchestration graph remains the single source of truth for *every* mutation
to the panel — additions from chat, additions from proposals, and interest
mirrors from approvals all flow through one place.

Composite score (deterministic, fast, legible):

    composite = len(interested) * 10        # primary: social proof
              + recency_decay                # secondary: 5 → 0 over 24h
              + base_score                   # tiebreak: surface origin

Higher = closer to the top. The 10x weight on interest means a single vote
beats any combination of recency + base_score, so the panel visibly reorders
the moment someone clicks "I'm in" on a related proposal or proposes an
idea from the panel.

Booked plans never appear here — the frontend dismisses them on book and
`snapshot()` filters dismissed ideas out before this node ever sees them.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..state import RankingState


_INTEREST_WEIGHT = 10.0
_RECENCY_MAX = 5.0
_RECENCY_HORIZON_HOURS = 24.0


def _parse_ts(ts: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _recency_decay(seen_at: str, now: datetime) -> float:
    dt = _parse_ts(seen_at)
    if dt is None:
        return 0.0
    age_hours = max(0.0, (now - dt).total_seconds() / 3600.0)
    if age_hours >= _RECENCY_HORIZON_HOURS:
        return 0.0
    return _RECENCY_MAX * (1.0 - age_hours / _RECENCY_HORIZON_HOURS)


def composite_score(idea: dict, *, now: datetime | None = None) -> float:
    """Public so callers (and tests) can sanity-check the panel order."""
    now = now or datetime.now(timezone.utc)
    interested = idea.get("interested") or []
    base = float(idea.get("score") or 0)
    return len(interested) * _INTEREST_WEIGHT + _recency_decay(idea.get("seen_at", ""), now) + base


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _merge_addition(ideas: list[dict], add: dict) -> list[dict]:
    """Add a new {event, source, base_score} triple, deduping on event id."""
    event = add.get("event") or {}
    eid = event.get("id")
    if not eid:
        return ideas
    source = add.get("source") or "reactive"
    base_score = int(add.get("base_score") or 0)

    for i in ideas:
        if i.get("event", {}).get("id") == eid:
            i["dismissed"] = False
            if base_score > int(i.get("score") or 0):
                i["score"] = base_score
            return ideas

    ideas.append({
        "event": event,
        "source": source,
        "score": base_score,
        "seen_at": _now_iso(),
        "interested": [],
        "dismissed": False,
    })
    return ideas


def _apply_interaction(ideas: list[dict], action: dict) -> list[dict]:
    eid = action.get("event_id")
    uid = action.get("user_id")
    kind = action.get("kind") or "interest_on"
    if not eid or not uid:
        return ideas
    for i in ideas:
        if i.get("event", {}).get("id") != eid:
            continue
        interested: list[str] = list(i.get("interested") or [])
        if kind == "interest_off":
            interested = [u for u in interested if u != uid]
        else:  # interest_on (default) — idempotent add
            if uid not in interested:
                interested.append(uid)
        i["interested"] = interested
        return ideas
    return ideas


def ranking_node(state: RankingState) -> RankingState:
    ideas = list(state.get("ideas") or [])

    for add in state.get("additions") or []:
        ideas = _merge_addition(ideas, add)
    for action in state.get("interactions") or []:
        ideas = _apply_interaction(ideas, action)

    now = datetime.now(timezone.utc)
    ideas.sort(key=lambda i: -composite_score(i, now=now))

    return {**state, "ideas": ideas}
