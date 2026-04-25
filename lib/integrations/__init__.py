"""External-service integrations.

Each module here wraps exactly one third-party system. Keep them small and
swappable so the agents and orchestrator stay vendor-neutral.

- asi_one         — Fetch.ai ASI:One LLM (OpenAI-compatible)
- google_calendar — Google Calendar OAuth + freebusy + insert
- agentverse      — Agentverse address registry + helpers
"""
