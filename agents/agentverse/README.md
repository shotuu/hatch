# Hatch — group hangout planner (Chat Protocol)

**Hatch** turns a dead group chat into a booked plan: overlapping free time,
ranked LA ideas, one-tap group approval, and Google Calendar writes for
everyone.

## Keywords (Agentverse / ASI:One discovery)

`group chat`, `hangout planner`, `Los Angeles`, `LA plans`, `weekend plans`,
`Google Calendar`, `group scheduling`, `coordination`, `Fetch.ai`, `Chat Protocol`,
`multi-agent`, `LangGraph`, `nest warmth`, `book together`

## What this uAgent does

- Speaks **Fetch Chat Protocol** so **ASI:One** and Agentverse can message it.
- Proxies intents to the local **FastAPI** app (`python server.py`): same
  `GroupState` as the phone-frame web UI — proposals and bookings show up live
  in both surfaces.

## Run locally

From the **repository root** (so `lib/` resolves):

```bash
# Terminal 1 — API + shared state
python server.py

# Terminal 2 — uAgent (different port than SERVER_PORT)
HATCH_UAGENT_PORT=8001 python -m agents.agentverse.main
```

Point ASI:One / Agentverse Inspector at the printed agent address. Ensure
`AGENTVERSE_API_KEY` and `AGENT_SEED_PHRASE` are set in `.env`.

If the API is not on `127.0.0.1:8005`, set e.g.:

```bash
export HATCH_API_BASE_URL=http://127.0.0.1:8005
```

## Example phrases (ASI:One)

- **Top board pick (proactive shortcut):** “Hatch a plan”, “find us something to do” — posts whatever is **#1 on the Ideas panel** (does not parse your sentence).
- **Topic-specific ideas (reactive, same as Hatch chat):** “Any ideas for a hiking trip?”, “down for brunch Saturday?” — proxied as a group message; Hatch runs **trigger + event synthesis** on that text.
- **Promote a reactive option to the pinned plan (same as “Propose to group”):** after a reactive card exists, say **“propose the first option”**, **“propose option 2”**, **“pick the second suggestion”**, etc. Uses the **latest** reactive bubble’s `matches` list (1-based).
- **Book:** “Book it”, “lock it in”, “pull the trigger”

Optional: `HATCH_PROXY_USER_ID=daniel` — which user id `POST /send_message` uses for reactive proxying (defaults to first user in `/state`).

**ASI:One @mentions:** messages often look like `@agent1qfw…n3 propose the 1st option`. The handle ends in a digit, so `3` and `propose` are both “word” characters and there is **no** `\b` before `propose` — the uAgent strips `@…` tokens before intent parsing so `propose_pick` still matches.

## Prize alignment

- **Agentverse:** registered agent + mailbox + manifest.
- **Chat Protocol:** `chat_protocol_spec` on inbound `ChatMessage`.
- **ASI:One:** natural-language entry; orchestration runs in the Hatch backend
  (LangGraph + Google Calendar API).
