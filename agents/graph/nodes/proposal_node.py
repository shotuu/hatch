"""Proposal composition node (Proposer agent role).

Phase 2: return a deterministic template string (no ASI:One call yet).
Phase 3+: replace this with `lib.integrations.asi_one` (or OpenAI-compatible)
to produce a short friend-voice message.
"""

from __future__ import annotations

from ..state import GraphState


def proposal_node(state: GraphState) -> GraphState:
    if not state.get("ok", True):
        return state

    window = state.get("window")
    event = state.get("event")
    if not window or not event:
        return {**state, "ok": False, "reason": "missing window or event"}

    # Keep copy short and camera-friendly. This is a placeholder until ASI:One.
    proposal_text = (
        f"You're all free {window['start']} to {window['end']}. "
        f"There's {event.get('title', 'something fun')} at {event.get('location', 'LA')} — want me to set it up?"
    )

    return {**state, "ok": True, "proposal_text": proposal_text}

