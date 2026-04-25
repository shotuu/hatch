"""Event synthesis node — calls ASI:One to discover real LA venues live.

This node owns:
  - the SYSTEM prompt that pins the model to *real* venues (no hallucinated URLs)
  - the ASI:One call (via lib.integrations.asi_one)
  - normalization into the dict shape the rest of the graph + UI consumes
  - a per-query cache so demo replays are instant and deterministic

We deliberately do NOT fall back to a curated events.json — the project decision
is "live LLM discovery only". If ASI:One returns nothing or errors out, the node
returns an empty match list and the format node renders an empty bubble (the
trigger node usually catches this earlier anyway).
"""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from urllib.parse import quote_plus
from uuid import uuid4

from lib.integrations import asi_one

from ..state import ReactiveState


_SYSTEM = """You are Hatch, a real-time event-discovery agent.
A friend group is chatting. Surface up to 3 plausible events that match the activity in the message.

CRITICAL — VENUE REALISM:
- Use ONLY real, verifiable venues you know from your training data.
- Default city: Los Angeles. Examples of real LA venues you know:
  Greek Theatre, Hollywood Bowl, The Wiltern, The Roxy, Crypto.com Arena, Dodger Stadium, BMO Stadium,
  Smorgasburg ROW DTLA, Grand Central Market, Apotheke (Chinatown), Resident (Arts District),
  Sushi Gen (Little Tokyo), Sea Harbour (Rosemead), Quarters Korean BBQ (Koreatown),
  Republique, Bavel, Bestia, Gjelina, Sqirl, Maude's Liquor Bar,
  The Comedy Store, Upright Citizens Brigade, Largo at the Coronet, The Improv,
  LACMA, MOCA, The Broad, Hauser & Wirth, Hammer Museum, Getty Center,
  Griffith Observatory, Runyon Canyon, Echo Park Lake, El Matador State Beach, Malibu Pier,
  The Stronghold (Lincoln Heights), Cliffs of Id,
  Tropicana Drive-In, Rooftop Cinema Club, Vidiots,
  UCLA campus venues if the message implies students.
- If the message implies a different city or country, use real venues there
  (e.g., "Tokyo ramen": Ichiran Shibuya, Afuri Roppongi; "Paris": Le Comptoir, etc.)
- If you DON'T KNOW a verifiably real venue for the activity, RETURN FEWER EVENTS. One real venue beats three fake ones. Empty array is acceptable.
- NEVER invent or guess venue names. NEVER append "LA" or "Los Angeles" to a fictional name to make it sound real.
- The neighborhood you give MUST be the venue's actual neighborhood.

OTHER RULES:
- Events occur in the next 14 days from "today"
- Mix price points; include free or cheap options where appropriate
- Tags lowercase snake_case (basketball, lakers, live_music, ramen, art, comedy, hikes, brunch, free, outdoor, indoor, ticketed)
- Datetime ISO 8601 with timezone offset (LA = -07:00 in summer)
- Title format: "{What} at {Venue}" or "{Venue}: {What}" — venue must be real

If the message is not actually about an activity (chitchat, greetings, feelings),
return {"events": []}.

Return EXACTLY this JSON shape:
{
  "events": [
    {
      "title": "...",
      "venue": "Real venue name only",
      "neighborhood": "Real neighborhood",
      "city": "Los Angeles",
      "datetime": "YYYY-MM-DDTHH:MM:00-07:00",
      "duration_minutes": 60,
      "price": 0,
      "tags": ["...", "..."]
    }
  ]
}"""


# Per-query cache. Keeps demo deterministic; survives the process lifetime.
_cache: dict[str, list[dict]] = {}
_cache_lock = Lock()


def _maps_url(venue: str, city: str) -> str:
    """Construct a Google Maps search URL — guaranteed valid, opens a real pin."""
    q = quote_plus(f"{venue} {city}".strip())
    return f"https://www.google.com/maps/search/?api=1&query={q}"


def _synthesize(message: str, n: int) -> list[dict]:
    """Ask ASI:One for up to N event candidates. Returns [] on failure."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    user = (
        f'Today: {today}\nMessage: "{message}"\n\n'
        f"Return up to {n} matching events with REAL venues you actually know."
    )

    try:
        # Lower temperature → factual recall over creativity.
        data = asi_one.chat_json(_SYSTEM, user, temperature=0.4, max_tokens=900)
        events = data.get("events", []) or []
    except Exception as e:
        print(f"[event_synth] ASI:One failed: {e}")
        return []

    out: list[dict] = []
    for e in events[:n]:
        if not isinstance(e, dict):
            continue
        venue = str(e.get("venue") or "").strip()
        if not venue:
            continue  # AI didn't commit to a real venue → drop
        neighborhood = str(e.get("neighborhood") or "").strip()
        city = str(e.get("city") or "Los Angeles").strip()
        location_parts = [p for p in [venue, neighborhood, city] if p]
        try:
            out.append({
                "id": f"ai_{uuid4().hex[:8]}",
                "title": str(e.get("title") or "")[:120],
                "datetime": str(e.get("datetime") or ""),
                "duration_minutes": int(e.get("duration_minutes") or 90),
                "location": ", ".join(location_parts),
                "price": float(e.get("price") or 0),
                "url": _maps_url(venue, city),
                "tags": [str(t).lower() for t in (e.get("tags") or [])][:6],
                "venue": venue,
            })
        except Exception:
            continue
    return out


def event_synth_node(state: ReactiveState) -> ReactiveState:
    if not state.get("should_react"):
        return {**state, "matches": []}

    text = (state.get("text") or "").strip()
    if not text:
        return {**state, "matches": []}

    key = text.lower()
    with _cache_lock:
        cached = _cache.get(key)
    if cached is not None:
        return {**state, "matches": cached[:3]}

    matches = _synthesize(text, n=3)

    with _cache_lock:
        _cache[key] = matches
    return {**state, "matches": matches}
