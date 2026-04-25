# Hatch — LA Hacks 2026

> Plans, hatched.

A group chat that expires unless you actually use it, with a multi-agent system
that turns dying threads into booked plans. See [CLAUDE.md](CLAUDE.md) for the
full brief — it's the source of truth.

## Quickstart

```bash
# 1. secrets
cp .env.example .env
# fill in ASI_API_KEY, AGENTVERSE_API_KEY, GOOGLE_CLIENT_ID/SECRET

# 2. backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python server.py                          # FastAPI on :8000

# 3. frontend (new terminal)
cd web && npm install && npm run dev      # Vite on :5173

# 4. (per teammate) Google Calendar OAuth
python -m lib.integrations.google_calendar authorize maya
python -m lib.integrations.google_calendar authorize jordan
# ...
```

Open http://localhost:5173 → tap **Trigger silence** → the agent's pinned
proposal eases in at the top.

## Repo map

```
agents/                       uAgents entrypoints (Chat Protocol)
  ├── proposer_agent.py       full template — composes the in-chat suggestion
  ├── calendar_agent.py       stub — wraps freebusy
  ├── event_agent.py          stub — ranks curated events
  └── booking_agent.py        stub — writes calendars + confirms

lib/
  ├── matching.py             pure helpers — find_overlap, rank_events
  └── integrations/           swap-in surface for every external service
      ├── asi_one.py            Fetch.ai ASI:One LLM (OpenAI-compatible)
      ├── google_calendar.py    Google OAuth + freebusy + event insert
      └── agentverse.py         agent address registry

data/
  ├── users.json              4 hardcoded users + interests
  ├── events.json             ~50 curated LA events (expand to 50)
  └── tokens/                 Google OAuth tokens (gitignored)

server.py                     FastAPI bridge — /propose, /book, /react
orchestrator.py               sequential pipeline: Calendar → Event → Proposer → Booking
web/                          Vite + React + Tailwind + Framer Motion phone-frame UI
```

### Where to plug things in

- **New external service?** Add a module under `lib/integrations/`. Don't import
  it from agents directly — go through orchestrator so the agents stay vendor-neutral.
- **New Fetch.ai agent?** Add a stub in `agents/`, register it in
  `lib/integrations/agentverse.py`. Use `agentverse.<NAME>.address` in the
  orchestrator to send messages.
- **Google Calendar tokens** live at `data/tokens/<user_id>.json`. The path is
  declared in `data/users.json::google_token_path`.

## Track owners (hour 0–4)

- **A — Proposer agent on Agentverse:** [agents/proposer_agent.py](agents/proposer_agent.py).
  Follow the [Render deploy guide](https://innovationlab.fetch.ai/resources/docs/agentverse/deploy-agent-on-agentverse-via-render).
  Don't leave until it's discoverable in ASI:One.
- **B — Google Calendar OAuth:** [lib/integrations/google_calendar.py](lib/integrations/google_calendar.py).
  Goal: dump a real `freebusy.query` for 4 teammates.
- **C — Web UI:** [web/](web/). Phone frame is live.
- **D — Content:** [data/events.json](data/events.json) (expand to ~50) +
  [data/users.json](data/users.json) (swap emails for teammates' real Google accounts).

## Golden rule

If a teammate says "just for the demo, can we…" — the answer is no.
The demo script in [CLAUDE.md](CLAUDE.md) §6 is the contract.
