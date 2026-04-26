"""Proposal composition node (Proposer agent role).

Phase 5 — Generate the friend-voice "headline" with ASI:One.

What changes:
  - We still always produce a deterministic `proposal_text` template (the line
    the bubble has rendered since Phase 2). That stays as the demo-safe floor.
  - On top of that, we now ask ASI:One for ONE short, friend-voice sentence
    that opens the bubble. This is the "voice" layer; the structured event
    card stays the "data" layer.

Why a single short sentence (not full freeform):
  - The UI layout is fixed. We never want the LLM to invent a price, a venue,
    or a date — those come from the structured event object. The LLM only
    contributes vibe.
  - One short sentence is easy to validate, easy to fall back from, and never
    wraps awkwardly inside the phone frame.

Anti-hallucination contract on TIMING (the silence claim):
  - The LLM is told it may ONLY reference how long the chat has been silent
    if we explicitly pass a `silence` field, and must use that phrase verbatim.
  - `silence` is computed in Python from the most-recent user message's
    timestamp (ISO if real, or parsed from human-readable seed strings like
    "3 weeks ago"), and only included if it's >= 1 day.
  - We strip per-message timestamps out of the prompt context so there is no
    other place for the LLM to grab a number from.

If ASI:One fails for any reason (no key, network, malformed JSON), we return
`headline=None` and the UI silently renders only the existing body. The demo
never breaks because of an LLM hiccup.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone

from ..state import GraphState

_HEADLINE_SYSTEM = """You are Hatch, a group-chat planning agent that just decided to break the silence with a proposal.

Write ONE short sentence (max 22 words) in casual friend-group voice that nudges the group to commit to the proposed event.

VOICE:
- Sound like a friend in the chat, not a notification.
- Reference the proposed event by name AND ground it in real timing from the structured event context.
- End with a soft CTA ("y'all in?", "want me to pull the trigger?", "shall we?", "down?").
- No emoji. No exclamation points. No greetings ("hey y'all", "hi team"). No corporate phrasing.
- Lowercase-friendly is fine but don't fake-Gen-Z it.

HARD RULE — TIMING / SILENCE:
- A `silence` field MAY appear in the context. If it does, you MAY reference it ("it's been {silence}", "{silence} of silence and y'all are still here") and you MUST use it verbatim — do NOT change the number or the unit.
- If `silence` is NOT in the context, you MUST NOT claim how long the chat has been silent or quiet. No "it's been a while", no "it's been weeks", no "ages since y'all hung out". Just talk about the event.
- Never invent a number, duration, or date that isn't in the structured fields.

GOOD EXAMPLES (when silence: "3 weeks"):
- "it's been 3 weeks. lakers are home saturday — pull the trigger?"
- "3 weeks of silence and y'all are still free saturday. lakers vs warriors at crypto, shall we?"

GOOD EXAMPLES (no silence field):
- "lakers vs warriors saturday at 7:30 — y'all in?"
- "smorgasburg saturday morning looks like the move. down?"
- "free gallery opening at lacma friday night — shall we?"

BAD EXAMPLES (do not produce):
- "it's been three weeks." (when no silence field is provided — fabrication)
- "ages since y'all did anything together." (vague timing claim, also fabrication)
- "Hello team! I have found an exciting event for you all to attend!" (formal, exclamation)
- "🏀 LAKERS GAME 🏀 free your calendar! 🔥" (emoji, hype)
- "I think we should go to a Lakers game and also maybe get food and also..." (rambling)

Return strict JSON: {"headline": "..."}
No code fence. No prose."""


def _safe_name(member: dict) -> str:
    n = (member.get("name") or "").strip()
    return n.split()[0] if n else ""


_RELATIVE_RE = re.compile(
    r"(\d+)\s*(minute|hour|day|week|month|year)s?\s*ago", re.IGNORECASE
)


def _format_elapsed(delta_seconds: float) -> str | None:
    """Bucketed friend-readable phrase for an elapsed duration.

    Returns None for anything under a day — the LLM should NOT claim "silence"
    on a chat that's been active in the last 24 hours.
    """
    if delta_seconds < 86400:  # < 1 day
        return None
    days = int(delta_seconds // 86400)
    if days < 7:
        return f"{days} day" if days == 1 else f"{days} days"
    weeks = days // 7
    return f"{weeks} week" if weeks == 1 else f"{weeks} weeks"


def _parse_relative_phrase(s: str) -> str | None:
    """Parse a human-readable relative ts like '3 weeks ago' → '3 weeks'.

    Used for the demo seed messages whose `ts` is a string, not an ISO stamp.
    Anything under a day returns None (no fake silence claim).
    """
    m = _RELATIVE_RE.search(s)
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2).lower()
    if unit in ("minute", "hour"):
        return None
    if unit == "day" and n < 1:
        return None
    plural = "s" if n != 1 else ""
    return f"{n} {unit}{plural}"


def _silence_phrase() -> str | None:
    """How long since the most recent user message — verbatim phrase or None.

    The LLM is forbidden from inventing a silence claim. This function is the
    only legitimate source of one. Sources, in order:
      1. The most recent user message has an ISO timestamp → real elapsed time
         from `datetime.now(...) - msg.ts`. Returns None if < 1 day.
      2. The most recent user message has a human-readable ts ("2 weeks ago",
         used by the demo seed) → parse it as-is.
      3. Anything else → None (no claim).
    """
    try:
        from lib.group_state import store

        msgs = [m for m in store().messages if getattr(m, "kind", "") == "user"]
        if not msgs:
            return None
        ts = (getattr(msgs[-1], "ts", "") or "").strip()
        if not ts:
            return None

        try:
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            delta = (datetime.now(timezone.utc) - dt).total_seconds()
            return _format_elapsed(delta)
        except ValueError:
            pass

        return _parse_relative_phrase(ts)
    except Exception:
        return None


def _recent_message_texts(limit: int = 5) -> list[dict]:
    """Last N user message TEXTS for tone (no timestamps).

    Stripping `ts` is intentional — the LLM previously latched onto seed
    timestamps like "3 weeks ago" and parroted them back as fact. The only
    sanctioned timing source is the `silence` field. This list is just for
    voice (e.g. picking up "miss y'all" energy).
    """
    try:
        from lib.group_state import store

        msgs = [m for m in store().messages if getattr(m, "kind", "") == "user"]
        return [
            {
                "author": getattr(m, "author_id", "") or "",
                "text": (getattr(m, "text", "") or "").strip(),
            }
            for m in msgs[-limit:]
        ]
    except Exception:
        return []


def _members() -> list[dict]:
    try:
        from lib import matching

        return [{"id": u["id"], "name": u["name"]} for u in matching.load_users()]
    except Exception:
        return []


def _format_when(window: dict) -> str:
    try:
        s = datetime.fromisoformat(window["start"])
        e = datetime.fromisoformat(window["end"])
        same_day = s.date() == e.date()
        day = s.strftime("%a %b %-d")
        if same_day:
            return f"{day} {s.strftime('%-I:%M %p')}–{e.strftime('%-I:%M %p')}"
        return f"{day} {s.strftime('%-I:%M %p')} → {e.strftime('%a %-I:%M %p')}"
    except Exception:
        return f"{window.get('start', '')} – {window.get('end', '')}"


def _call_asi_one(
    *,
    event: dict,
    window: dict,
    recent: list[dict],
    members: list[dict],
    silence: str | None,
) -> str | None:
    try:
        from lib.integrations import asi_one

        names = ", ".join(filter(None, (_safe_name(m) for m in members))) or "the group"
        recent_lines = (
            "\n".join(f"  - {r['author']}: {r['text']}" for r in recent if r.get("text"))
            or "  (no recent messages)"
        )

        # `silence` is included as a structured field IFF we can verify it.
        # If it's None we omit the line entirely so the LLM has no string in
        # the prompt that mentions duration at all.
        silence_line = f"- Silence (verbatim, only field allowed for timing claims): {silence}\n" if silence else ""

        user_msg = (
            "Context:\n"
            f"- Group members: {names}\n"
            f"{silence_line}"
            f"- Recent message texts (no timestamps — for tone only):\n{recent_lines}\n"
            f"- Proposed event:\n"
            f"    title: {event.get('title', 'something fun')}\n"
            f"    venue: {event.get('venue') or event.get('location', 'LA')}\n"
            f"    when:  {_format_when(window)}\n"
            f"    price: ${event.get('price', 0)}\n"
            "Generate the headline."
        )
        out = asi_one.chat_json(_HEADLINE_SYSTEM, user_msg, temperature=0.65, max_tokens=120)
        headline = (out.get("headline") or "").strip()
        return headline or None
    except Exception as e:
        print(f"[proposal_node] headline LLM failed, falling back: {e}")
        return None


# Tiny in-process cache so demo replays of the same event at the same silence
# bucket return the same headline (no flicker, no extra LLM calls).
_HEADLINE_CACHE: dict[tuple[str, str], str] = {}


def _silence_bucket(phrase: str | None) -> str:
    """Cache-key bucket. Bucketing keeps the cache stable while real elapsed
    time creeps forward second-by-second."""
    if not phrase:
        return "none"
    if "week" in phrase or "month" in phrase or "year" in phrase:
        return "weeks"
    return "days"


def proposal_node(state: GraphState) -> GraphState:
    if not state.get("ok", True):
        return state

    window = state.get("window")
    event = state.get("event")
    if not window or not event:
        return {**state, "ok": False, "reason": "missing window or event"}

    silence = _silence_phrase()
    eid = event.get("id") or event.get("title") or ""
    cache_key = (eid, _silence_bucket(silence))

    headline = _HEADLINE_CACHE.get(cache_key)
    if headline is None and os.environ.get("ASI_API_KEY"):
        headline = _call_asi_one(
            event=event,
            window=window,
            recent=_recent_message_texts(),
            members=_members(),
            silence=silence,
        )
        if headline:
            _HEADLINE_CACHE[cache_key] = headline

    proposal_text = (
        f"You're all free {window['start']} to {window['end']}. "
        f"There's {event.get('title', 'something fun')} at {event.get('location', 'LA')} — want me to set it up?"
    )

    out: GraphState = {**state, "ok": True, "proposal_text": proposal_text}
    if headline:
        out["headline"] = headline
    return out
