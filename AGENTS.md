# LA Hacks 2026 — Project Brief for Codex

> Everything below is decided — don't relitigate.

---

## 1. Product

**Name:** Hatch — "plans, hatched."

**One-liner:** A group chat with a living nest — go silent and it cools, book plans together and it glows. An AI agent makes sure it stays warm.

**Elevator:** Group chats are where plans die. We're building an ambient multi-agent system that lives in a friend group's chat, knows everyone's calendars, and proactively turns dying threads into real booked plans. Not suggestions — bookings. The chat itself has a **nest** — a warmth meter that quietly cools during silence and is restored when the group books a plan together. The agent is the friend who always has an idea and actually follows through; the nest is the visible reward for letting them in.

**Thesis for judges:** Individual AI assistants are solved. Group coordination is still broken. This wouldn't have been buildable six months ago — Fetch.ai's Agentverse + Chat Protocol + ASI:One just made multi-agent orchestration a weekend project.

---

## 2. Hackathon Context

- **Event:** LA Hacks 2026, 36-hour hackathon at UCLA.
- **Deliverables:** project description, code repo, demo video (~90–120s), Devpost submission.
- **All four deliverables serve the demo video.** Judges watch the reel; they do not read the repo. Build backward from the 120-second script.

### Tracks targeted (priority order)
1. **Flicker to Flow** (LA Hacks main track) — "turn friction into function." Group scheduling is pure friction; we turn it into booked plans.
2. **Fetch.ai — Agentverse: Search & Discovery of Agents** — $2,500 / $1,500 / $1,000. Requires agents registered on Agentverse, discoverable via ASI:One, implementing **Chat Protocol (mandatory)**. Payment Protocol optional.
3. **MLH stackables (cheap/free wins):**
   - **Figma Make Challenge** — check the box on Devpost, show a screenshot of Make in the workflow. 15 min of effort.
   - **Best Domain Name from GoDaddy Registry** — pick the final name, register a domain.
   - **Best Use of MongoDB Atlas** — only if we actually use it. **Currently we don't need a DB. Skip.**

### Pitch framing (use these exact phrases)
- Flicker to Flow voice: "friction into function."
- Fetch.ai voice: "executable outcomes."
- Restraint angle: "quiet 99% of the time, perfect 1% of the time — the only AI you'd actually let into your group chat."

---

## 3. Tech Stack (LOCKED)

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.10+ | uAgents requirement |
| Agent framework | **uAgents** (Fetch.ai) | `pip install uagents uagents-core` |
| Protocol | **Chat Protocol** via `chat_protocol_spec` | mandatory for the prize |
| LLM (agent reasoning) | **ASI:One** via OpenAI-compatible SDK, `base_url="https://api.asi1.ai/v1"` | preferred for the prize |
| LLM (fallback, harder tasks) | Codex / GPT | only if ASI:One insufficient |
| Calendar | Google Calendar API | OAuth, `google-auth-oauthlib` + `google-api-python-client` |
| Events data | **Curated JSON** (~50 real LA events, hand-picked) | NO scraper, ever |
| Frontend | **Web app inside a phone-shaped frame** | Vite + React + Tailwind + Framer Motion. Max-width ~390px. **Light mode**, warm Hatch palette (cream + coral). NOT a native mobile app. |
| Hosting | Agents on Agentverse (Mailbox); frontend on Vercel | |
| DB | None (JSON files on disk) | |
| Voice / ElevenLabs | **NOT this weekend.** | Parked post-hackathon. Voice messages and call-listening are parked too. |

### Required env vars
```
ASI_API_KEY=...
AGENTVERSE_API_KEY=...
AGENT_SEED_PHRASE=...             # any stable string; deterministically generates agent address
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
ANTHROPIC_API_KEY=...             # fallback LLM, optional
```

Agentverse API key: set all scopes to **Write**. Mailbox + Chat Resources are required.

---

## 4. MVP Scope (RUTHLESSLY LOCKED)

Six things ship. Everything else is a "future work" slide.

1. 4 hardcoded users in one group chat. Real Google accounts (teammates).
2. One group with a **Trip Name** and a **nest meter** (0–30 warmth, decays during silence, restores on booking; default starts at 6 for the demo). Visible in chat header as a labeled pill + thin progress bar.
3. **Reactive AI mode:** when someone sends a message mentioning a concrete activity ("Lakers game next week"), a foldable AI reply appears threaded below with tickets/ETAs/propose-to-group button. Build this LAST — cut if behind.
4. **Proactive AI mode:** on silence trigger OR cooling-nest trigger, agent posts a full proposal pinned at top of chat. This is the hero flow.
5. **One-tap book:** writes the event to all 4 Google Calendars + posts a confirmation message + restores the nest to full warmth.
6. Nest meter visible in header; restores to full when a plan is booked. The nest never disappears — it just goes cold and asks to be warmed.

### NOT in the MVP (do not build)
- Real user account creation / auth / profiles / birthdays
- Real message-content inference of interests (interests come from **onboarding questionnaire**, which for the demo is a hardcoded JSON)
- Cross-group memory, sentiment-ranked panels, right-side idea panel
- Reactive-mode book-through (the "propose to group" button in reactive mode just opens the proactive-mode flow)
- Paid event checkout, real ticketing APIs
- Substitute-event logic ("that Lakers game passed, here's another…")
- Real event scraping from Eventbrite / any site
- Voice, video, mobile native
- Manual calendar entry (Google OAuth is the only path)

If a teammate suggests "just for the demo, can we…" — the answer is **no**.

---

## 5. Agent Architecture (4 agents + orchestrator, on Agentverse)

**Key scope cut:** the original plan had 5 agents. The **Interest agent got absorbed into the Event agent** (interest profiles are a JSON lookup, not a pipeline step).

Register **at least 3 agents on Agentverse** for the "multi-agent" prize check. The rest can be internal Python functions if time runs short. Judges inspect the Marketplace page, not the internal graph.

### Agents
1. **Calendar agent** — reads `freebusy.query` for 4 users, finds overlap windows ≥ N hours.
2. **Event agent** — queries curated `events.json`, ranks by interest-tag match against `users.json` interests.
3. **Proposer agent** — composes the in-chat suggestion message in natural friend-voice using ASI:One.
4. **Booking agent** — executes Google Calendar writes across 4 accounts, posts confirmation, restores nest warmth to full.

**Orchestrator:** routes sequentially via Chat Protocol — Calendar → Event → Proposer → (user tap) → Booking. No branching, no "alternative proposal" flow.

Each agent needs its own README/keywords on Agentverse for discoverability via ASI:One.

---

## 6. Demo Script (120 seconds — this is the contract)

**Pre-set state:** Phone frame open. Group: "LA Friends" (Maya, Jordan, Priya, you). Trip Name visible. Nest meter shows **🥚 Nest is cooling** with the bar near 20% full. Last message timestamp: **3 weeks ago**. 4 Google Calendar tabs pre-authed and open.

| Time | Beat | On screen |
|---|---|---|
| 0:00–0:15 | Hook | Presenter points at the cooling nest meter + silent chat. "Group chats are where plans die — and you can see this one cooling down in real time." |
| 0:15–0:35 | **Reactive mode** | Driver types as Maya: "anyone down for the Lakers game next week?" → folded AI reply appears under it with 3 ticket options. Expand → collapse. |
| 0:35–0:55 | **Silence + proactive** | Scroll up through dead chat. Agent pinned message appears: "Nest is cooling — let's hatch something. You're all free Sat 2–6pm. Free gallery opening in Arts District at 3pm. Want me to set it up?" with `[Book it] [Show me something else] [Not this weekend]` |
| 0:55–1:25 | **The one tap** | Tap **Book it** → animated checklist (RSVP, 4 calendar writes) → switch to Google Calendar tab, show event live → switch back. Nest meter animates from cooling → glowing (full bar, ✨ pill). Agent posts: "Booked. Nest is glowing — see you there." |
| 1:25–1:50 | Pitch | "Under the hood: 4 agents on Fetch.ai's Agentverse coordinating via Chat Protocol, discoverable via ASI:One." Mention Flicker to Flow + Fetch.ai thesis verbatim. |
| 1:50–2:00 | Close | Tagline: "Plans, hatched." |

**Risky moment:** Google Calendar API write (0:55–1:25). API can lag 8+ seconds. **Record a flawless backup video by hour 30.** If live fails, cut to video mid-sentence.

Every click must be rehearsed 10+ times. Driver should do it blindfolded by hour 34.

### Silence trigger mechanic
- **Demo:** hardcoded "3 weeks ago" timestamp + a cooling nest meter + a button that fires the orchestrator when tapped. Presenter narrates: "The agent's ambient monitor watches the nest cool and fires the pipeline before it goes cold." Don't build a real timer.
- **Production (when judges ask):** lightweight watcher decays nest warmth as time-since-last-message grows; agent triggers at low warmth + free-window availability. No polling in the demo.

---

## 7. Hour-by-hour Build Plan

### Hour 0–4: parallel tracks, 4 teammates
- **Track A (blocking):** first teammate ships a registered `proposer_agent` on Agentverse, responding to chat via ASI:One + Chat Protocol. Copy the [Render deployment example](https://innovationlab.fetch.ai/resources/docs/agentverse/deploy-agent-on-agentverse-via-render) verbatim. Don't move on until it works.
- **Track B:** Google Calendar OAuth. External consent screen, Testing mode, add 4 teammates as test users. Goal: dump `freebusy.query` JSON for all 4 accounts.
- **Track C:** Vite + React phone-frame UI. Hardcoded messages, stubbed `/propose` endpoint returns static JSON. Deploy to Vercel immediately.
- **Track D:** content. `events.json` (50 events hand-curated from Eventbrite / Do LA / UCLA), `users.json` (4 teammates, 5–8 interest tags each from a fixed vocabulary). Pure matching functions.

**Hour 4 checkpoint:** vertical slice working — phone UI calls FastAPI → calls proposer_agent → returns proposal with real data. If not working, cut agents; make orchestrator a plain Python function; register agents later for prize compliance.

### Hour 4–20: flesh out until demo script runs cleanly end to end.
### Hour 20–28: polish only what the camera sees (phone CSS, message copy, avatars, confirmation animation).
### Hour 28–32: record demo (multiple takes), write Devpost, **submit at hour 32**.
### Hour 32–36: buffer. Live pitch rehearsal, fixes.

---

## 8. Decisions / Privacy / Edge cases

- **User model for demo:** one user acts on behalf of the group (not N simultaneous logins).
- **Interests source:** onboarding questionnaire (hardcoded JSON for demo). NOT inferred from chat messages. This is the answer to any judge's privacy question.
- **LLM calls:** transient. Nothing stored.
- **Data:** per-group, not cross-group.
- **Approval button:** lives **inside the agent's chat bubble** (Slack-style interactive message). Not a separate UI element.
- **Nest restore:** booking a plan restores the nest to full warmth. The chat itself never expires — only the warmth decays — so users see growth they're proud of, not a threat hanging over them. The agent is the chat's lifeline.

---

## 9. How Codex should respond

- Be concise. Hackathon time is precious.
- Challenge scope creep aggressively. If I ask to add a feature, ask what it replaces.
- Prioritize shipping over elegance. Ugly code that demos beats beautiful code that doesn't.
- When writing code, assume uAgents + Chat Protocol patterns. Point me at Fetch.ai docs if uncertain.
- For architecture questions: 36-hour constraint first, scalability never.
- Tie pitch-facing copy back to "friction into function" (Flicker to Flow) and "executable outcomes" (Fetch.ai).
- Flag when I'm about to spend time on something judges won't see.
- If something breaks at hour 30, cut it — don't fix it. The demo script is the contract.

---

## 10. Open questions

- Domain registration for `hatch` — coordinate with the GoDaddy MLH track.
- Role split among 4 teammates (suggested: one per Track A/B/C/D for hour 0–4, then converge).
- Hosted Agentverse agents vs. locally-run agents for the live demo (local is more reliable for demo but less impressive for the Agentverse prize — register at least 3 on hosted Agentverse for the prize check).
- Exact event corpus sources (current plan: hand-curated from Eventbrite + UCLA events + a few LA venues).
