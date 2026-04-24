"""Pure matching functions — free/busy overlap + interest-ranked events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@dataclass
class Window:
    start: datetime
    end: datetime

    @property
    def duration_minutes(self) -> int:
        return int((self.end - self.start).total_seconds() // 60)


def load_users() -> list[dict]:
    return json.loads((DATA_DIR / "users.json").read_text())


def load_events() -> list[dict]:
    return json.loads((DATA_DIR / "events.json").read_text())


def find_overlap(
    busy_by_user: dict[str, list[tuple[datetime, datetime]]],
    search_start: datetime,
    search_end: datetime,
    min_minutes: int = 120,
) -> list[Window]:
    """Return windows within [search_start, search_end] where every user is free for >= min_minutes.

    busy_by_user: {user_id: [(busy_start, busy_end), ...]} — from Google freebusy.query.
    """
    merged: list[tuple[datetime, datetime]] = []
    for intervals in busy_by_user.values():
        merged.extend(intervals)
    merged.sort(key=lambda x: x[0])

    free: list[Window] = []
    cursor = search_start
    for b_start, b_end in merged:
        if b_end <= cursor:
            continue
        if b_start > cursor:
            w = Window(cursor, min(b_start, search_end))
            if w.duration_minutes >= min_minutes:
                free.append(w)
        cursor = max(cursor, b_end)
        if cursor >= search_end:
            break
    if cursor < search_end:
        w = Window(cursor, search_end)
        if w.duration_minutes >= min_minutes:
            free.append(w)
    return free


def rank_events(
    events: Iterable[dict],
    users: Iterable[dict],
    windows: list[Window],
) -> list[dict]:
    """Rank events by interest overlap across users AND fit into a free window."""
    tag_weight: dict[str, int] = {}
    for u in users:
        for t in u.get("interests", []):
            tag_weight[t] = tag_weight.get(t, 0) + 1

    ranked = []
    for e in events:
        score = sum(tag_weight.get(t, 0) for t in e.get("tags", []))
        if score == 0:
            continue
        start = datetime.fromisoformat(e["datetime"])
        end = start + timedelta(minutes=e["duration_minutes"])
        fits = any(w.start <= start and w.end >= end for w in windows)
        if not fits and windows:
            continue
        ranked.append({**e, "_score": score})
    ranked.sort(key=lambda e: (-e["_score"], e["datetime"]))
    return ranked
