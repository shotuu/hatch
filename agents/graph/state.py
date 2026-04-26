"""Shared state for LangGraph workflow.

LangGraph nodes pass a single state object forward. Treat each node as a
"specialist agent" with one responsibility that reads/writes parts of state.

For Phase 2 (scaffolding), the state mirrors the existing orchestrator output:
  - a chosen overlap window
  - ranked events (top N)
  - a proposal text string (template for now)

Later phases will extend this state with:
  - trigger classification outputs (reactive mode)
  - mentions/ideas list updates
  - booking results (after explicit approval)
"""

from __future__ import annotations

from typing import NotRequired, TypedDict


class WindowDict(TypedDict):
    start: str
    end: str


class GraphState(TypedDict):
    """Minimum state to produce a proposal plan."""

    # Inputs
    search_hours: NotRequired[int]
    min_window_minutes: NotRequired[int]

    # Outputs / intermediate
    users: NotRequired[list[dict]]
    windows: NotRequired[list[WindowDict]]
    window: NotRequired[WindowDict]
    ranked: NotRequired[list[dict]]
    event: NotRequired[dict]
    alternates: NotRequired[list[dict]]
    proposal_text: NotRequired[str]
    # ASI:One-generated friend-voice opener that renders above the structured
    # event card. Optional — if absent, the bubble falls back to body-only.
    headline: NotRequired[str]

    # Standard status envelope (keeps calling code simple)
    ok: NotRequired[bool]
    reason: NotRequired[str]


class IdeaDict(TypedDict):
    """Wire shape of an idea (matches lib.group_state.Idea after asdict)."""

    event: dict
    source: str
    score: int
    seen_at: str
    interested: list[str]
    dismissed: bool


class InteractionDict(TypedDict, total=False):
    """A user action on an idea: 'I'm in' toggle from approve / propose."""

    event_id: str
    user_id: str
    kind: str  # "interest_on" | "interest_off"


class RankingState(TypedDict):
    """State for the ideas-panel ranking workflow.

    The node is pure: it takes the current ideas list plus a delta (new events
    to add and/or interactions to apply) and returns the merged, re-sorted list.

    No LLM call. Lives as a graph node purely for orchestration consistency —
    every UI-visible state change for the panel runs through one place. Phase
    8+ can drop in a `cluster_node` to merge near-duplicates without touching
    any caller.
    """

    ideas: NotRequired[list[IdeaDict]]
    additions: NotRequired[list[dict]]  # {event, source, base_score}
    interactions: NotRequired[list[InteractionDict]]


class BookingState(TypedDict):
    """State for the booking workflow (Phase 6).

    Inputs:
      - event_id: id of the event to book (resolved from proposal / panel /
        events.json by `eligibility_node`)

    Intermediate / outputs:
      - event: the resolved event dict (title, datetime, duration, location)
      - users: [{id, name, google_token_path}] for everyone in the group
      - calendars_written: count of calendar entries that landed (real OR
        demo-safe mocks for users without tokens — see calendar_writer_node)
      - mocked: of those, how many were mocks. mocked == calendars_written
        means no real Google writes happened (demo-safe path)
      - failures: per-user error strings for real writes that threw
      - nest_restore: target nest warmth value to set after a successful book
    """

    event_id: str
    event: NotRequired[dict]
    users: NotRequired[list[dict]]

    calendars_written: NotRequired[int]
    mocked: NotRequired[int]
    failures: NotRequired[list[str]]
    nest_restore: NotRequired[int]

    ok: NotRequired[bool]
    reason: NotRequired[str]


class ReactiveState(TypedDict):
    """State for the reactive (per-message) workflow.

    Inputs:
      - text: the user's chat message
      - parent_id: id of the message we're reacting to (for threading)

    Intermediate / outputs:
      - should_react: trigger node decision (rules / LLM)
      - matches: list of structured event candidates (from ASI:One synthesis)
      - reply: UI-shaped payload {headline, options[]} for the chat bubble
    """

    text: str
    parent_id: NotRequired[str]
    should_react: NotRequired[bool]
    matches: NotRequired[list[dict]]
    reply: NotRequired[dict]
