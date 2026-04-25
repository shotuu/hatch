"""LangGraph workflow builder.

We keep the graphs linear for hackathon reliability:
  proposal graph: availability → event_select → proposal → END

Booking stays out of this graph intentionally. The product contract requires an
explicit user action ("Book it") before any calendar writes happen.
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, StateGraph

from .state import GraphState, RankingState, ReactiveState
from .nodes.availability_node import availability_node
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

