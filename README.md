# Hatch — LA Hacks 2026

> Plans, hatched.

A group chat with a living **nest** — a warmth meter that cools during silence
and is restored when the group books a plan together. An ambient multi-agent
system watches the nest, surfaces real LA events that match everyone's
calendars, and turns one tap into four Google Calendar bookings. The chat never
dies — only the nest cools, and the agent's job is to keep it warm.

Calendars + curated LA events + a friend-voice proposer, glued together over
Fetch.ai's Chat Protocol. See [CLAUDE.md](CLAUDE.md) for the full brief — it's
the source of truth for scope and pitch.

## Quickstart

```bash
# 1. secrets — create a .env in the repo root with:
#    ASI_API_KEY=...
#    AGENTVERSE_API_KEY=...        # only needed for USE_REMOTE_AGENTS=1
#    AGENT_SEED_PHRASE=...
#    GOOGLE_CLIENT_ID=...
#    GOOGLE_CLIENT_SECRET=...
#    ANTHROPIC_API_KEY=...         # optional fallback
#    USE_REMOTE_AGENTS=0           # 0 = local pipeline, 1 = Agentverse agents

# 2. backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python server.py                              # FastAPI on :8000

# 3. frontend (new terminal)
cd web && npm install && npm run dev          # Vite on :5173

# 4. (per teammate) Google Calendar OAuth — drops a token at data/tokens/<id>.json
python -m lib.integrations.google_calendar authorize daniel
python -m lib.integrations.google_calendar authorize jono
python -m lib.integrations.google_calendar authorize andrew
```

Open http://localhost:5173 → pick the **LA Friends** chat → tap the demo panel's
**Trigger silence** (or type a message that hints at an activity) → the agent's
pinned proposal eases in at the top. Tap **Approve** as each user — when all
approve, booking fires and writes the event to every Google Calendar.

## How it runs end-to-end

```
phone UI ──poll /state──▶  server.py  ──▶  orchestrator.propose_plan()
   │                          │                  │
   │                          │                  ├─ LOCAL  : lib.matching + lib.integrations
   │                          │                  └─ REMOTE : Agentverse agents via Chat Protocol
   │                          │
   ├──/send_message──▶  group_state ──▶  event_synthesis.find_reactive_matches
   │                                       (foldable AI reply under the message)
   │
   └──/approve (×N) ──▶  all_approved? ──▶  orchestrator.book_plan()
                                              ├─ writes 4 Google Calendars
                                              └─ restores nest warmth, posts confirmation
```

Toggle local vs. remote with `USE_REMOTE_AGENTS=1`. Demo rule: live tap-through
runs LOCAL (fast, no flakes); record a separate clip showing REMOTE for the
Agentverse prize narrative.

## Repo map

```
agents/                       uAgents entrypoints (Chat Protocol)
  ├── proposer_agent.py         composes the in-chat suggestion via ASI:One
  ├── calendar_agent.py         freebusy → overlap windows
  ├── event_agent.py            ranks curated events against interests
  ├── booking_agent.py          calendar writes + confirmation
  └── agentverse/main.py        single deployable hosted-agent entrypoint

lib/
  ├── matching.py               find_overlap, rank_events (pure)
  ├── event_synthesis.py        reactive: message → matched events
  ├── group_state.py            singleton in-memory chat store (messages,
  │                             proposal lifecycle, approvals, ideas, nest warmth)
  ├── protocol.py               Pydantic models exchanged between agents
  └── integrations/             swap-in surface for every external service
      ├── asi_one.py              Fetch.ai ASI:One LLM (OpenAI-compatible)
      ├── google_calendar.py      OAuth + freebusy + insert + cleanup
      ├── agentverse.py           agent-address registry
      └── agent_client.py         Chat Protocol client used by orchestrator

services/                     legacy / scratch wrappers — kept for reference
  ├── google_calender.py        (note: spelling)
  └── openai_client.py

scripts/
  ├── cleanup_calendars.py      bulk-delete every "Hatch · …" event
  └── print_addresses.py        dump registered agent addresses

data/
  ├── users.json                hardcoded users + interest tags
  ├── events.json               curated LA events
  └── tokens/                   Google OAuth tokens (gitignored)

server.py                     FastAPI bridge — see endpoints below
orchestrator.py               Calendar → Event → Proposer → (tap) → Booking
                              with LOCAL / REMOTE dispatch
web/                          Vite + React + Tailwind + Framer Motion
                              phone-frame UI (light mode, ~390px wide)
```

## Server endpoints

| Method | Path                | Purpose                                                    |
|--------|---------------------|------------------------------------------------------------|
| GET    | `/health`           | basic ping; reports `use_remote_agents` flag               |
| GET    | `/state`            | full snapshot — messages, proposal, ideas, nest, users     |
| POST   | `/reset`            | wipe state back to seed (demo reset)                       |
| POST   | `/send_message`     | append a user message; auto-runs reactive matcher          |
| POST   | `/react`            | manually trigger reactive synthesis on a query             |
| POST   | `/propose`          | run the orchestrator and stash a proposal in state         |
| POST   | `/approve`          | one user approves; when all approve, booking fires         |
| POST   | `/dismiss_proposal` | skip the active proposal                                   |
| POST   | `/swap_alternate`   | rotate to the next ranked event                            |
| POST   | `/propose_idea`     | promote an entry from the ideas panel into a proposal      |
| POST   | `/dismiss_idea`     | hide an idea from the side panel                           |
| POST   | `/cleanup`          | bulk-delete `Hatch · *` events from all 4 calendars        |
| GET    | `/users`            | dump `data/users.json`                                     |
| GET    | `/events`           | dump `data/events.json`                                    |

The phone polls `/state` every ~1s; mutations happen via the dedicated POSTs.
Restart `server.py` = clean slate (state is in-memory).

## Where to plug things in

- **New external service?** Add a module under `lib/integrations/`. Don't import
  it from agents directly — go through orchestrator so agents stay vendor-neutral.
- **New Fetch.ai agent?** Add a stub in `agents/`, register it in
  `lib/integrations/agentverse.py`, and consume via `agent_client` from the
  orchestrator's REMOTE path.
- **New ranking signal?** Extend `lib/matching.rank_events` (LOCAL) and the
  `event_agent` (REMOTE) — they should stay symmetric.
- **Google Calendar tokens** live at `data/tokens/<user_id>.json`. The path is
  declared in `data/users.json::google_token_path`.

## Track owners (hour 0–4 reference, kept for posterity)

- **A — Proposer agent on Agentverse:** [agents/proposer_agent.py](agents/proposer_agent.py)
  + [agents/agentverse/main.py](agents/agentverse/main.py). Follow the
  [Render deploy guide](https://innovationlab.fetch.ai/resources/docs/agentverse/deploy-agent-on-agentverse-via-render).
- **B — Google Calendar OAuth:** [lib/integrations/google_calendar.py](lib/integrations/google_calendar.py).
- **C — Web UI:** [web/](web/). Phone frame is live.
- **D — Content:** [data/events.json](data/events.json) +
  [data/users.json](data/users.json).

## Golden rule

If a teammate says "just for the demo, can we…" — the answer is no.
The demo script in [CLAUDE.md](CLAUDE.md) §6 is the contract.
