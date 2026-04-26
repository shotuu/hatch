# Hatch

> Plans, hatched.

Hatch is a group-chat planning prototype built for LA Hacks 2026. It gives a
friend group's chat a living "nest" that cools during silence and warms back up
when the group books a plan together.

The prototype combines a phone-frame web UI, a FastAPI backend, LangGraph
orchestration, Fetch.ai uAgents, ASI:One, curated LA event data, and Google
Calendar writes. The core demo flow turns a cooling group chat into a concrete
proposal and, after group approval, writes the event to each configured member's
calendar.

## What Works

- Three hardcoded group members in a shared "LA Friends" chat.
- A visible nest warmth meter from `0` to `30`.
- Seeded dead-chat state for the demo, including "3 weeks ago" messages.
- Reactive replies when a message mentions an activity, powered by ASI:One
  event synthesis and rendered as foldable options in the chat.
- Proactive proposals triggered manually or automatically when the nest cools.
- Ranked "ideas in the air" panel with interest and hide signals.
- Group approval flow with optimistic UI updates.
- Booking pipeline that writes to Google Calendar when OAuth tokens exist and
  mock-confirms missing-token users for demo reliability.
- Agentverse-compatible Chat Protocol entrypoint for ASI:One discovery.
- Demo utilities for resetting state, seeding calendar conflicts, clearing
  Hatch calendar events, and adjusting nest warmth.

## Architecture

```text
React phone UI
  ├─ polls /api/state every ~1s
  ├─ sends chat messages and approvals
  └─ drives demo controls

FastAPI backend (server.py)
  ├─ owns shared in-memory GroupState
  ├─ exposes chat, proposal, booking, and demo endpoints
  └─ dispatches orchestration through orchestrator.py

LangGraph workflows
  ├─ proposal: availability -> event_select -> proposal
  ├─ reactive: trigger -> event_synth -> format
  ├─ ranking: rank
  └─ booking: eligibility -> write_calendars

Integrations
  ├─ ASI:One for friend-voice proposal headlines and reactive event discovery
  ├─ Google Calendar for free/busy checks, fixture seeding, cleanup, and writes
  └─ Fetch.ai uAgents + Chat Protocol for Agentverse / ASI:One access
```

By default, the live demo uses the local LangGraph path for speed and
reliability. Set `USE_REMOTE_AGENTS=1` to route proposal and booking requests
through Agentverse-hosted agents via Chat Protocol, with a local fallback if the
remote path fails.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Python, FastAPI, Pydantic |
| Orchestration | LangGraph |
| Agents | Fetch.ai `uagents`, Chat Protocol |
| LLM | ASI:One through an OpenAI-compatible client |
| Calendar | Google Calendar API + OAuth token files |
| Frontend | Vite, React, TypeScript, Tailwind CSS, Framer Motion |
| Storage | JSON files and in-memory process state |

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google OAuth credentials if you want real calendar reads/writes
- ASI:One API key if you want LLM-generated headlines and reactive discovery

### Environment

Create `.env` in the repository root:

```bash
ASI_API_KEY=...
AGENTVERSE_API_KEY=...
AGENT_SEED_PHRASE=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Optional
USE_REMOTE_AGENTS=0
USE_LANGGRAPH=1
ALLOW_MOCK_CALENDAR=1
SERVER_PORT=8005
```

Important runtime flags:

- `USE_REMOTE_AGENTS=0` keeps proposal and booking on the local LangGraph path.
- `USE_REMOTE_AGENTS=1` tries Agentverse agents first and falls back locally.
- `USE_LANGGRAPH=1` is the current default orchestration path.
- `ALLOW_MOCK_CALENDAR=1` allows proposal generation when calendar OAuth tokens
  are missing.
- `SERVER_PORT` defaults to `8005`; the Vite proxy reads this value from the
  root `.env`.

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

The API runs on `http://127.0.0.1:8005` by default.

### Frontend

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:5173`. The frontend calls backend routes through the
Vite `/api` proxy.

### Google Calendar OAuth

Authorize each demo user once. Tokens are stored under `data/tokens/` and are
ignored by git.

```bash
python -m lib.integrations.google_calendar authorize daniel
python -m lib.integrations.google_calendar authorize jono
python -m lib.integrations.google_calendar authorize andrew
```

User IDs and token paths are configured in `data/users.json`.

## Demo Flow

1. Start the backend and frontend.
2. Open the phone-frame UI at `http://localhost:5173`.
3. Use the dev console to reset chat state or adjust nest warmth.
4. Drop the nest warmth to `3` or below, or call `POST /propose`, to trigger the
   proactive agent.
5. The agent pins a proposal from the top-ranked idea.
6. Tap approval as each group member.
7. After everyone approves, the booking workflow writes calendar events where
   tokens exist, mock-confirms missing-token users, posts a celebration message,
   and restores the nest to full warmth.

Reactive mode is also available: send an activity-like message such as
`anyone down for the Lakers game next week?` and Hatch renders AI-synthesized
options under the message.

## API Reference

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check and remote-agent flag. |
| `GET` | `/state` | Shared chat snapshot for the phone UI. |
| `POST` | `/reset` | Reset in-memory demo state. |
| `POST` | `/send_message` | Add a user message and optionally run reactive synthesis. |
| `POST` | `/react` | Manually run the reactive pipeline for a query. |
| `POST` | `/propose` | Run the proactive proposal workflow. |
| `POST` | `/approve` | Mark one user as approved; schedules booking after all approve. |
| `POST` | `/dismiss_proposal` | Skip the active proposal. |
| `POST` | `/set_warmth` | Set nest warmth and optionally auto-propose when cold. |
| `POST` | `/swap_alternate` | Swap the active proposal to the next alternate. |
| `POST` | `/propose_idea` | Promote an idea-panel item into the pinned proposal. |
| `POST` | `/dismiss_idea` | Globally remove an idea from the panel. |
| `POST` | `/hide_idea` | Hide an idea for one user and lower its ranking. |
| `POST` | `/cleanup` | Delete `Hatch · ...` calendar events for all configured users. |
| `GET` | `/calendar_demo/status` | Check seeded calendar fixture status. |
| `POST` | `/calendar_demo/seed` | Seed demo busy blocks into calendars. |
| `POST` | `/calendar_demo/delete` | Remove demo busy blocks. |
| `GET` | `/users` | Return `data/users.json`. |
| `GET` | `/events` | Return `data/events.json`. |

State is intentionally in-memory. Restarting `server.py` gives the prototype a
clean process, and `POST /reset` restores the seeded demo chat.

## Agentverse / Chat Protocol

The Agentverse-compatible entrypoint lives in `agents/agentverse/main.py`. It
speaks Fetch.ai Chat Protocol and proxies natural-language intents into the
same FastAPI backend used by the phone UI.

Run it locally from the repository root:

```bash
python server.py
HATCH_UAGENT_PORT=8001 python -m agents.agentverse.main
```

Useful environment variables:

- `HATCH_API_BASE_URL=http://127.0.0.1:8005` if the API is not on the default.
- `HATCH_PROXY_USER_ID=daniel` to choose which user ASI:One proxy messages use.

Supported ASI:One-style intents include:

- "hatch a plan" or "find us something to do" -> proactive proposal.
- "any ideas for hiking?" -> reactive event discovery.
- "propose the first option" -> promote the latest reactive option.
- "book it" or "lock it in" -> approve/book the current proposal.

See `agents/agentverse/README.md` for the Agentverse listing copy and examples.

## Repository Structure

```text
agents/
  agentverse/                 Chat Protocol uAgent entrypoint and intent parser
  graph/                      LangGraph state, workflows, and nodes
  calendar_agent.py           Calendar role for remote-agent path
  event_agent.py              Event-ranking role for remote-agent path
  proposer_agent.py           Friend-voice proposer role
  booking_agent.py            Calendar booking role

lib/
  group_state.py              Shared in-memory chat, proposal, ideas, and nest state
  matching.py                 JSON loading, overlap windows, and event ranking
  protocol.py                 Pydantic request/response models for agents
  integrations/
    agent_client.py           Chat Protocol client for remote agents
    agentverse.py             Agent address registry
    asi_one.py                ASI:One client wrapper
    google_calendar.py        OAuth, free/busy, insert, cleanup, and fixtures

data/
  users.json                  Demo group members, colors, interests, token paths
  events.json                 Curated LA event corpus
  tokens/                     Local Google OAuth tokens, ignored by git

web/
  src/                        React phone-frame UI and demo console
  vite.config.ts              Dev server and /api proxy

server.py                     FastAPI app
orchestrator.py               Local/remote dispatch and reactive helpers
requirements.txt              Python dependencies
```

## Scripts

```bash
python scripts/print_addresses.py
python scripts/chat_ping.py
python scripts/cleanup_calendars.py
```

Calendar cleanup is also available through `POST /cleanup` and the frontend dev
console.

## Prototype Notes

- No database is used; persistent data lives in `data/*.json`.
- Calendar tokens are local files and should never be committed.
- Booking is explicit: the system only writes calendars after group approval.
- Missing calendar tokens are mocked during booking so the filmed demo remains
  smooth, while real token/API failures are surfaced in the booking result.
- The frontend is intentionally a web app inside a phone-shaped frame, not a
  native mobile app.
- Voice, payment checkout, real ticket purchase, scraping, auth, and cross-group
  memory are outside the finalized prototype.
