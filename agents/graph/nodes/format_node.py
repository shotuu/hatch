"""Format node — turn raw matches into the UI-shaped reactive reply payload.

The web UI renders reactive messages from `ChatMessage.matches` directly, so we
already match its expected shape (list of events with title/location/etc.). To
keep a clean contract for ASI:One / Agentverse callers, we *also* produce a
`reply` envelope with a stable shape:

    {
      "headline": "Found N options for \"<query>\"",
      "options": [{"id", "title", "subtitle", "cta"}, ...]
    }

The headline is generated deterministically from the count + query so the LLM
never invents copy that diverges from the cards below it.
"""

from __future__ import annotations

from datetime import datetime

from ..state import ReactiveState


def _human_subtitle(event: dict) -> str:
    parts: list[str] = []
    if event.get("location"):
        parts.append(str(event["location"]))
    dt_raw = event.get("datetime")
    if dt_raw:
        try:
            dt = datetime.fromisoformat(dt_raw)
            parts.append(dt.strftime("%a, %b %d"))
        except Exception:
            parts.append(str(dt_raw))
    price = event.get("price")
    if price is not None:
        try:
            parts.append("Free" if float(price) == 0 else f"${float(price):.0f}")
        except Exception:
            pass
    return " · ".join(parts)


def format_node(state: ReactiveState) -> ReactiveState:
    matches = state.get("matches") or []
    query = (state.get("text") or "").strip()

    if not matches:
        return {**state, "reply": {"headline": "", "options": []}}

    options = [
        {
            "id": e.get("id") or f"opt_{i}",
            "title": e.get("title") or "",
            "subtitle": _human_subtitle(e),
            "cta": "Propose to group",
        }
        for i, e in enumerate(matches)
    ]
    n = len(options)
    headline = f'Found {n} option{"s" if n != 1 else ""} for "{query}"'
    return {**state, "reply": {"headline": headline, "options": options}}
