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
    window: NotRequired[WindowDict]
    ranked: NotRequired[list[dict]]
    event: NotRequired[dict]
    alternates: NotRequired[list[dict]]
    proposal_text: NotRequired[str]

    # Standard status envelope (keeps calling code simple)
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

