"""AI-grounded novel events — uses ASI:One trained knowledge of real venues.

The AI is instructed to use ONLY venues it knows are real (LA-default, worldwide
if the message implies it). URLs are constructed server-side as Google Maps
search links so every "see location" tap opens a real pin — no hallucinated
broken URLs.

Cached by query → demo determinism.
"""
from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from urllib.parse import quote_plus
from uuid import uuid4

from lib import matching
from lib.integrations import asi_one


SYSTEM = """You are Hatch, a real-time event-discovery agent.
A friend group is chatting. Surface up to 3 plausible events that match the activity in the message.

CRITICAL — VENUE REALISM:
- Use ONLY real, verifiable venues you know from your training data.
- Default city: Los Angeles. Examples of real LA venues you know:
  Greek Theatre, Hollywood Bowl, The Wiltern, The Roxy, Crypto.com Arena, Dodger Stadium, BMO Stadium,
  Smorgasburg ROW DTLA, Grand Central Market, Apotheke (Chinatown), Resident (Arts District),
  Sushi Gen (Little Tokyo), Sea Harbour (Rosemead), Quarters Korean BBQ (Koreatown),
  Republique, Bavel, Bestia, Gjelina, Sqirl, Republique, Maude's Liquor Bar,
  The Comedy Store, Upright Citizens Brigade, Largo at the Coronet, The Improv,
  LACMA, MOCA, The Broad, Hauser & Wirth, Hammer Museum, Getty Center,
  Griffith Observatory, Runyon Canyon, Echo Park Lake, El Matador State Beach, Malibu Pier,
  The Stronghold (Lincoln Heights), Cliffs of Id, Stronghold,
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


_ACTIVITY_HINTS = (
    "wanna", "want to", "want", "anyone", "down for", "down to", "let's", "lets ",
    "should we", "we should", "looking for", "going to", "go to",
    "tonight", "tomorrow", "weekend", "saturday", "sunday", "friday",
    "next week", "this week", "?",
)

_STOPWORDS = {
    "the", "and", "for", "any", "you", "all", "are", "was", "but", "not",
    "can", "now", "out", "anyone", "down", "who", "want", "going", "with",
    "this", "that", "have", "yall", "y'all", "guys", "lol", "lmk", "fr",
}

_cache: dict[str, list[dict]] = {}
_cache_lock = Lock()


def looks_like_activity(text: str) -> bool:
    t = text.lower()
    if len(t.split()) < 3:
        return False
    return any(h in t for h in _ACTIVITY_HINTS)


def find_reactive_matches(message: str, *, n: int = 3) -> list[dict]:
    """Best-effort match: AI synthesis with real venues, curated keyword fallback."""
    if not looks_like_activity(message):
        return []

    key = message.strip().lower()
    with _cache_lock:
        if key in _cache:
            return _cache[key][:n]

    events = _synthesize_via_ai(message, n=n)
    if not events:
        events = _fallback_curated(message, n=n)

    with _cache_lock:
        _cache[key] = events
    return events


def _maps_url(venue: str, city: str) -> str:
    """Construct a Google Maps search URL — guaranteed valid, opens a real pin."""
    q = quote_plus(f"{venue} {city}".strip())
    return f"https://www.google.com/maps/search/?api=1&query={q}"


def _synthesize_via_ai(message: str, n: int) -> list[dict]:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    user = f'Today: {today}\nMessage: "{message}"\n\nReturn up to {n} matching events with REAL venues you actually know.'

    try:
        # Lower temperature → factual recall over creativity
        data = asi_one.chat_json(SYSTEM, user, temperature=0.4, max_tokens=900)
        events = data.get("events", []) or []
    except Exception as e:
        print(f"[synthesis] AI failed: {e}")
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


def _fallback_curated(message: str, n: int) -> list[dict]:
    """When AI is down, do a smarter keyword search than v1 string-contains."""
    text = message.lower()
    terms = [t.strip("?!.,'\"") for t in text.split()]
    terms = [t for t in terms if len(t) >= 4 and t not in _STOPWORDS]
    if not terms:
        return []

    scored: list[tuple[int, dict]] = []
    for e in matching.load_events():
        haystack = (e["title"] + " " + " ".join(e["tags"])).lower()
        hits = sum(1 for t in terms if t in haystack)
        if hits:
            scored.append((hits, e))
    scored.sort(key=lambda x: -x[0])
    return [e for _, e in scored[:n]]
