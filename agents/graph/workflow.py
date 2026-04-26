"""LangGraph workflow builder.

We keep the graphs linear for hackathon reliability:
  proposal graph: availability → event_select → proposal → END
  reactive graph: trigger → event_synth → format → END
  ranking graph:  rank → END
  booking graph:  eligibility → write_calendars → END

Booking is its own graph (not glued onto proposal) because the product
contract requires an explicit user action ("Book it") between the two — no
auto-bookings, ever.
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, StateGraph

from .state import BookingState, GraphState, RankingState, ReactiveState
from .nodes.availability_node import availability_node
from .nodes.calendar_writer_node import calendar_writer_node
from .nodes.eligibility_node import eligibility_node
from .nodes.event_select_node import event_select_node
from .nodes.event_synth_node import event_synth_node
from .nodes.format_node import format_node
from .nodes.proposal_node import proposal_node
from .nodes.ranking_node import ranking_node
from .nodes.trigger_node import trigger_node


@lru_cache(maxsize=1)
def proposal_graph():
    """Compiled graph for generating a proposal plan."""

    g = StateGraph(GraphState)

    g.add_node("availability", availability_node)
    g.add_node("events", event_select_node)
    g.add_node("proposal", proposal_node)

    g.set_entry_point("availability")
    g.add_edge("availability", "events")
    g.add_edge("events", "proposal")
    g.add_edge("proposal", END)

    return g.compile()


@lru_cache(maxsize=1)
def reactive_graph():
    """Compiled graph for per-message reactive replies.

    Pipeline: trigger → event_synth → format → END.
    The trigger node short-circuits chitchat so we don't waste an LLM call
    on every message; downstream nodes return empty payloads when skipped.
    """

    g = StateGraph(ReactiveState)

    g.add_node("trigger", trigger_node)
    g.add_node("event_synth", event_synth_node)
    g.add_node("format", format_node)

    g.set_entry_point("trigger")
    g.add_edge("trigger", "event_synth")
    g.add_edge("event_synth", "format")
    g.add_edge("format", END)

    return g.compile()


@lru_cache(maxsize=1)
def ranking_graph():
    """Compiled graph for the ideas-panel ranking pipeline.

    Single node today (`ranking_node` does dedupe + composite sort). Phase 8+
    can drop in a `cluster_node` to merge near-duplicates without changing
    any caller — the graph stays the seam.
    """

    g = StateGraph(RankingState)
    g.add_node("rank", ranking_node)
    g.set_entry_point("rank")
    g.add_edge("rank", END)
    return g.compile()


@lru_cache(maxsize=1)
def booking_graph():
    """Compiled graph for the booking workflow (Phase 6).

    Pipeline: eligibility → write_calendars → END.

      - eligibility: resolves the event_id to a real event (proposal / panel
        / events.json), pulls the group member list. Fails fast if anything's
        missing so write_calendars never runs on partial state.
      - write_calendars: per-user Google Calendar inserts with a demo-safe
        mock fallback when a user's OAuth token isn't on disk.

    Lives separate from `proposal_graph` because the product contract
    requires explicit user approval between proposing and booking.
    """

    g = StateGraph(BookingState)
    g.add_node("eligibility", eligibility_node)
    g.add_node("write_calendars", calendar_writer_node)
    g.set_entry_point("eligibility")
    g.add_edge("eligibility", "write_calendars")
    g.add_edge("write_calendars", END)
    return g.compile()

