# Plans — LA Hacks 2026

Group chat that expires unless you actually use it, with a multi-agent system
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
python server.py           # FastAPI on :8000

# 3. frontend (new terminal)
cd web && npm install && npm run dev    # Vite on :5173
```

Open http://localhost:5173 → tap **Trigger agent (demo)** → agent proposal
appears pinned at the top.

## Track owners (hour 0–4)

- **A — Proposer agent on Agentverse:** `agents/proposer_agent.py`. Follow
  the [Render deploy guide](https://innovationlab.fetch.ai/resources/docs/agentverse/deploy-agent-on-agentverse-via-render).
  Don't leave until it's discoverable in ASI:One.
- **B — Google Calendar OAuth:** `lib/calendar_client.py`. Goal: dump a real
  `freebusy.query` for 4 teammates.
- **C — Web UI:** `web/`. Phone frame is live; polish copy + animations
  (nothing functional needs changing).
- **D — Content:** `data/events.json` (expand to ~50 real LA events) +
  `data/users.json` (swap emails for teammates' real Google accounts).

## Repo map

```
agents/         uAgents entrypoints (Chat Protocol)
lib/            pure helpers — asi_client, matching, calendar_client
data/           users.json, events.json, tokens/ (gitignored)
server.py       FastAPI bridge (/propose, /book)
orchestrator.py sequential pipeline (Calendar → Event → Proposer → Booking)
web/            Vite + React + Tailwind phone-frame UI
```

## Golden rule

If a teammate says "just for the demo, can we…" — the answer is no.
The demo script in `CLAUDE.md` §6 is the contract.
