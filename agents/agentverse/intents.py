"""Intent classification for ASI:One → Hatch uAgent (Phase 7).

The web UI calls explicit REST endpoints. ASI:One only sends free text over
Chat Protocol, so we need a tiny router:

  book     — confirm the current pending plan (calendar writes)
  reactive — specific activity / "any ideas for X" → same pipeline as typing
             in the Hatch group chat (`/send_message` + LangGraph reactive)
  propose  — **only** strong global phrases ("hatch a plan", "find us something")
             → `POST /propose`, which posts the **top-ranked panel idea** (not
             derived from this sentence — by design that path has no query text)
  propose_pick — promote the Nth option from the **latest reactive bubble** to
    the pinned group plan (`POST /propose_idea`, same as "Propose to group" in
    the UI). Checked before `reactive` so "propose the first hiking …" doesn't
    get swallowed by the hiking keyword alone.
  chitchat — everything else

Why "reactive" is separate from "propose":
  `/propose` runs the proactive planner (availability → top **panel** pick →
  headline). It never sees ASI:One's words. Asking "any ideas for hiking?" was
  wrongly classified as propose, so you got the Lakers game again — same as
  "hatch a plan" because both hit `/propose`. Activity-style questions must go
  through `/send_message` so `trigger_node` + `event_synth_node` can use the
  actual text (hiking, Lakers, etc.).
"""

from __future__ import annotations

import re
from typing import Literal

Intent = Literal["propose", "book", "reactive", "propose_pick", "chitchat"]


def normalize_inbound(text: str) -> str:
    """Strip ASI:One / Slack-style @mentions so regexes see real words.

    Agent handles look like ``@agent1qfwa5...n3`` and end with a digit. That
    digit is a ``\\w`` char, so ``3propose`` has **no** ``\\b`` before
    ``propose`` — ``parse_reactive_pick_index`` would miss and ``propose_pick``
    would never fire. Removing ``@...`` tokens fixes that class of bugs.
    """
    t = (text or "").strip()
    t = re.sub(r"@\S+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


_ORDINAL_TO_N: dict[str, int] = {
    "first": 1,
    "1st": 1,
    "second": 2,
    "2nd": 2,
    "third": 3,
    "3rd": 3,
    "fourth": 4,
    "4th": 4,
}

_BOOK_HINTS = re.compile(
    r"\b("
    r"book\s+it|book\s+this|book\s+that|"
    r"lock\s*it\s*in|"
    r"go\s+ahead|"
    r"pull\s+the\s+trigger|"
    r"schedule\s+it|"
    r"confirm\s+(the\s+)?(plan|booking)|"
    r"yes\s*,?\s*book|"
    r"put\s+it\s+on\s+(the\s+)?calendar|"
    r"add\s+it\s+to\s+(everyone'?s?\s+)?calendar"
    r")\b",
    re.I,
)

# Strong global propose only — each of these intentionally maps to POST /propose
# (top panel idea). Do NOT put "any ideas" here; that must not call /propose.
_PROPOSE_HINTS = re.compile(
    r"\b("
    r"hatch\s+(a\s+)?plan|"
    r"find\s+(us\s+)?(something|a\s+plan)|"
    r"need\s+a\s+plan|"
    r"plan\s+something|"
    r"suggest\s+(something|a\s+hangout)|"
    r"weekend\s+plans|"
    r"set\s+us\s+up|"
    r"give\s+us\s+a\s+plan"
    r")\b",
    re.I,
)

# Activity / open-ended planning language → same as messaging the group chat.
_REACTIVE_HINTS = re.compile(
    r"("
    r"any\s+ideas\s+for|"
    r"suggestions?\s+for|"
    r"ideas\s+for(\s+a|\s+the|\s+some|\s+our)?\b|"
    r"what\s+about|"
    r"how\s+about|"
    r"thinking\s+about|"
    r"want\s+to\s+go|"
    r"down\s+for|"
    r"anyone\s+want|"
    r"\b(hiking|hike|trail|trails|trek|ski|skiing|snowboard|beach|surf|"
    r"concert|museum|gallery|brunch|breakfast|lunch|dinner|camping|kayak|"
    r"kayaking|climb|climbing|pickleball|tennis|golf|spa|yoga)\b"
    r")",
    re.I,
)


def parse_reactive_pick_index(text: str) -> int | None:
    """1-based index into the **latest** reactive bubble's `matches` list.

    Returns None if this message isn't asking to promote a specific option.
    """
    low = normalize_inbound(text).lower()
    if len(low) < 4:
        return None

    m = re.search(r"\bpropose\s+option\s*(\d+)\b", low)
    if m:
        return max(1, int(m.group(1)))

    m = re.search(r"\bpropose\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)\b", low)
    if m:
        return max(1, int(m.group(1)))

    m = re.search(r"\bpropose\s+(?:the\s+)?#(\d+)\b", low)
    if m:
        return max(1, int(m.group(1)))

    m = re.search(
        r"\bpropose\s+(?:the\s+)?(first|second|third|fourth|1st|2nd|3rd|4th)\b",
        low,
    )
    if m:
        return _ORDINAL_TO_N.get(m.group(1))

    m = re.search(
        r"\b(pick|use)\s+(?:the\s+)?(first|second|third|fourth|1st|2nd|3rd|4th|\d+)\b"
        r'(?:\s+(?:option|one|match|suggestion|idea))?',
        low,
    )
    if m:
        word = m.group(2)
        if word.isdigit():
            return max(1, int(word))
        return _ORDINAL_TO_N.get(word)

    return None


def classify_intent(text: str) -> Intent:
    t = normalize_inbound(text)
    if len(t) < 2:
        return "chitchat"
    low = t.lower()
    if _BOOK_HINTS.search(low):
        return "book"
    if parse_reactive_pick_index(t) is not None:
        return "propose_pick"
    if _REACTIVE_HINTS.search(low):
        return "reactive"
    if _PROPOSE_HINTS.search(low):
        return "propose"
    return "chitchat"
