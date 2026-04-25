"""LangGraph orchestration layer (internal multi-agent workflow).

This package implements the "multi-agent" pipeline as LangGraph nodes.
We keep it internal (called by FastAPI + Agentverse entrypoints) so the same
workflow powers both the web demo and ASI:One / Agentverse.
"""

