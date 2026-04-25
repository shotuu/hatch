"""Wipe Hatch-created events from every user's Google Calendar.

Only touches events tagged with the Hatch marker (extendedProperties.private.source=hatch).
User-created events are never touched.

Usage:
    python -m scripts.cleanup_calendars              # delete with confirmation
    python -m scripts.cleanup_calendars --dry-run    # list what would go
    python -m scripts.cleanup_calendars --yes        # skip confirmation
    python -m scripts.cleanup_calendars --user daniel  # one user only
"""
from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from lib import matching
from lib.integrations import google_calendar

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="list, don't delete")
    p.add_argument("--yes", action="store_true", help="skip confirmation")
    p.add_argument("--user", help="restrict to one user id")
    args = p.parse_args()

    users = matching.load_users()
    if args.user:
        users = [u for u in users if u["id"] == args.user]
        if not users:
            print(f"no such user: {args.user}")
            return

    # Preview pass — list everything first.
    plan: list[tuple[dict, list[dict]]] = []
    total = 0
    for u in users:
        token_rel = u["google_token_path"]
        if not (ROOT / token_rel).exists():
            print(f"  · {u['name']}: no token (skipping)")
            continue
        items = google_calendar.list_hatch_events(token_rel)
        plan.append((u, items))
        total += len(items)
        print(f"  · {u['name']}: {len(items)} Hatch event(s)")
        for ev in items:
            start = ev.get("start", {}).get("dateTime", "?")
            print(f"      - {ev.get('summary', '(no title)')}  {start}")

    if total == 0:
        print("\nNothing to clean up.")
        return

    print(f"\nTotal: {total} event(s) across {len(plan)} user(s).")
    if args.dry_run:
        print("(dry-run — nothing deleted)")
        return

    if not args.yes:
        confirm = input("Delete all of these? [y/N] ").strip().lower()
        if confirm not in ("y", "yes"):
            print("Aborted.")
            return

    deleted = 0
    for u, items in plan:
        for ev in items:
            try:
                google_calendar.delete_event(u["google_token_path"], ev["id"])
                deleted += 1
            except Exception as e:
                print(f"  ! {u['name']} / {ev.get('summary')}: {e}")
    print(f"\nDeleted {deleted}/{total}.")


if __name__ == "__main__":
    main()
