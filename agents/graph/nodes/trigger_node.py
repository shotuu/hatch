"""Trigger node — decides whether the agent should react to a chat message.

Two-stage gate, cheap-first:

  1. Keyword heuristic (`_looks_like_activity`) — zero-latency rules-based
     short-circuit. Catches the obvious cases ("anyone down for the lakers
     game tonight?") without burning an LLM call.
  2. LLM fallback (`_llm_thinks_activity`) — only runs when stage 1 says no.
     Asks ASI:One to classify with a deliberately strict prompt biased toward
     False. Catches the long tail ("crypto.com arena thursday") that the
     keyword list will never cover, without us having to keep growing the
     keyword list every time someone phrases something differently.

Both stages must be cheap to skip in the no-text / sub-3-word case.

Owning the rules here (instead of importing from a shared module) means each
LangGraph node is fully self-describing — judges see a real specialist agent.
"""

from __future__ import annotations

from threading import Lock

from lib.integrations import asi_one

from ..state import ReactiveState


# Phrases that suggest a planning intent. Tuned for casual group-chat voice.
_ACTIVITY_HINTS: tuple[str, ...] = (
    "wanna", "want to", "want", "anyone", "down for", "down to", "let's", "lets ",
    "should we", "we should", "looking for", "going to", "go to",
    "tonight", "tomorrow", "weekend", "saturday", "sunday", "friday",
    "next week", "this week", "?",
)


def _looks_like_activity(text: str) -> bool:
    t = text.lower()
    if len(t.split()) < 3:
        return False
    return any(h in t for h in _ACTIVITY_HINTS)


# Strict, opinionated prompt. The bias is heavy toward NO — Hatch is "quiet
# 99% of the time, perfect 1% of the time"; a false positive is worse than a
# missed reaction. Concrete examples on both sides keep the model anchored.
_TRIGGER_SYSTEM = """You are the activation gate for Hatch, a group-chat planning agent.

Your only job: decide whether the most recent user message is a SPECIFIC, ACTIONABLE planning intent that warrants surfacing real-world event options to the group.

Return strict JSON: {"should_react": true|false}. No prose, no other keys.

REACT (true) only if the message clearly references a concrete activity, place, event, show, or outing the group could do together — even if phrased casually. Examples:
- "anyone down for the lakers game next week?" → true
- "miss going to the museum lol" → true (clear venue + nostalgic = surface options)
- "crypto.com arena thursday" → true (venue + day, even with no verb)
- "down to grab boba this weekend" → true
- "we should hike runyon again" → true

DO NOT REACT (false) for everything else. When in doubt, return false. Examples:
- "lol", "fr", "yeah", "wyd" → false (small talk)
- "miss y'all" → false (no activity)
- "i'm so tired" → false (state, not intent)
- "what time is it" → false (info question)
- "did you see the news" → false (topic, not plan)
- "i went to the lakers game last night" → false (past, not future)
- "kobe was so good" → false (opinion / nostalgia, no activity)

Bias: when ambiguous, return false. A missed reaction is recoverable; a noisy reaction breaks trust."""


# Cache LLM verdicts on identical message text. Cheap belt-and-suspenders for
# the demo (e.g. judges typing the same probe twice) and keeps total spend
# bounded if a teammate spams the same message during rehearsal.
_llm_cache: dict[str, bool] = {}
_llm_cache_lock = Lock()


def _llm_thinks_activity(text: str) -> bool:
    key = text.lower().strip()
    with _llm_cache_lock:
        if key in _llm_cache:
            return _llm_cache[key]

    try:
        result = asi_one.chat_json(
            _TRIGGER_SYSTEM,
            f"Most recent user message:\n{text}",
            temperature=0.0,
            max_tokens=20,
        )
        verdict = bool(result.get("should_react"))
    except Exception as e:
        # Fail closed — a missing key, network blip, or malformed response
        # should never make the agent louder. Log and bail to False.
        print(f"[trigger_node] LLM fallback failed, defaulting to False: {e}")
        verdict = False

    with _llm_cache_lock:
        _llm_cache[key] = verdict
    return verdict


def trigger_node(state: ReactiveState) -> ReactiveState:
    text = (state.get("text") or "").strip()
    if not text or len(text.split()) < 3:
        return {**state, "should_react": False}

    if _looks_like_activity(text):
        return {**state, "should_react": True}

    return {**state, "should_react": _llm_thinks_activity(text)}
