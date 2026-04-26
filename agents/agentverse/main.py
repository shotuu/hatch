"""Hatch orchestrator uAgent — Chat Protocol + ASI:One / Agentverse (Phase 7).

This process is the **public bridge** from ASI:One into the same LangGraph-backed
state the web UI uses:

  1. Create a uAgent (stable seed → address) with mailbox mode.
  2. Register Fetch **Chat Protocol** so ASI:One speaks the same message shapes.
  3. On each inbound `ChatMessage`, classify intent → call the local FastAPI
     server (`python server.py`) over HTTP → reply with a short text summary.

The phone-frame UI does **not** require this agent — it talks to FastAPI
directly. Run both when you want the Fetch track demo: ASI:One messages Hatch,
the group chat updates in real time from the shared `GroupState`.

Env (see also `server_client.py`):
  AGENT_SEED_PHRASE, AGENTVERSE_API_KEY, HATCH_NETWORK, HATCH_UAGENT_PORT
  HATCH_API_BASE_URL or HATCH_API_HOST + SERVER_PORT (default port 8005)

Docs:
  https://innovationlab.fetch.ai/resources/docs/agent-communication/chat-protocol
  https://uagents.fetch.ai/docs/guides/chat_protocol

Run locally (from repo root, with server already up):
  python -m agents.agentverse.main
"""
from __future__ import annotations

import os
import traceback
from datetime import datetime, timezone
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

from agents.agentverse.intents import classify_intent, normalize_inbound, parse_reactive_pick_index
from agents.agentverse.server_client import (
    api_base_url,
    fetch_state,
    health_check,
    post_approve_all,
    post_propose,
    post_propose_idea,
    post_send_message,
)

load_dotenv()

agent = Agent(
    name=os.environ.get("HATCH_UAGENT_NAME", "hatch-main"),
    seed=os.environ.get("AGENT_SEED_PHRASE", "hatch-main-dev-seed-change-me"),
    network=os.environ.get("HATCH_NETWORK", "mainnet"),
    port=int(os.environ.get("HATCH_UAGENT_PORT", "8000")),
    mailbox=True,
    publish_agent_details=True,
)

chat_proto = Protocol(spec=chat_protocol_spec)

_CHITCHAT = (
    "Hatch here — try: \"hatch a plan\" (top board pick), activity questions like "
    "\"any ideas for hiking?\", \"propose the first option\" after reactive results, "
    "or \"book it\" on the pending plan. Keep `python server.py` running with the phone UI."
)

_OFFLINE = (
    f"I can't reach the Hatch API at {api_base_url()} — start `python server.py` "
    "from the repo root, then message me again."
)


def _propose_ok_reply(state: dict) -> str:
    p = state.get("current_proposal") or {}
    ev = p.get("event") or {}
    title = (ev.get("title") or "a plan").strip()
    return (
        f"Posted in the group chat: {title}. "
        "That's the #1 idea on the group's board right now — the short \"hatch a plan\" shortcut "
        "doesn't read your ASI:One wording; for something specific like hiking, ask in that style "
        "and I'll route it through the idea finder. Open the Hatch UI to vote I'm in, or say \"book it\" here for the demo."
    )


def _last_reactive_message(state: dict) -> dict | None:
    for m in reversed(state.get("messages") or []):
        if m.get("kind") == "reactive":
            return m
    return None


def _propose_pick_reply(state: dict, index: int) -> str:
    rmsg = _last_reactive_message(state)
    if not rmsg:
        return (
            "No reactive suggestion card in the chat yet — ask something like "
            "\"any ideas for hiking?\" first, then say \"propose the first option\"."
        )
    matches = rmsg.get("matches") or []
    if not matches:
        return "The last Hatch suggestion had no options to promote — try a new question in the Hatch chat."
    if index > len(matches):
        return (
            f"There are only {len(matches)} option(s) in the latest card — "
            f"you asked for #{index}."
        )
    ev = matches[index - 1]
    title = (ev.get("title") or "that option").strip()
    return (
        f"Promoted option {index} to the group plan: {title}. "
        "Open the Hatch UI for approvals, or say \"book it\" here to approve everyone for the demo."
    )


def _reactive_followup_reply(state: dict, inbound: str) -> str:
    """Summarize the last reactive bubble after we proxied text via /send_message."""
    msgs = state.get("messages") or []
    if not msgs:
        return "Message posted, but the chat state looks empty — refresh the Hatch UI."
    last = msgs[-1]
    if last.get("kind") != "reactive":
        return (
            "Your line was posted to the Hatch group chat, but the reactive agent didn't fire "
            "(no activity match). Try something more concrete, use the Hatch app, or say "
            "\"hatch a plan\" here to post the top-ranked group pick."
        )
    matches = last.get("matches") or []
    q = last.get("query") or inbound
    if not matches:
        return (
            f"Hatch looked for {q!r} but didn't find confident matches. "
            "Try naming a venue or a day, or open the Hatch UI for the full empty-state card."
        )
    top = matches[0]
    title = (top.get("title") or "an option").strip()
    n = len(matches)
    return (
        f"Hatch found {n} option(s) for {q!r} — lead pick: {title}. "
        "Open the Hatch phone UI for tickets, times, and Propose to group."
    )


def _propose_fail_reply(plan: dict) -> str:
    r = plan.get("reason") or plan.get("detail") or "unknown error"
    return f"Couldn't hatch a plan — {r}. Check the API is up at {api_base_url()}."


def _book_ok_reply(payload: dict) -> str:
    booking = payload.get("booking") or {}
    ok = booking.get("ok", True)
    cw = int(booking.get("calendars_written") or 0)
    mocked = int(booking.get("mocked") or 0)
    fails = booking.get("failures") or []
    if not ok and cw == 0:
        return (
            "Everyone approved, but zero calendars wrote successfully. "
            f"Details: {'; '.join(str(f) for f in fails[:3]) or booking.get('reason', 'unknown')}. "
            "Check OAuth tokens under data/tokens/."
        )
    base = f"Booked — {cw} calendar(s) updated. Nest should be glowing in the Hatch UI."
    if mocked and mocked == cw:
        base += " (All demo mocks — add OAuth tokens under data/tokens/ for real Google writes.)"
    elif mocked:
        base += f" ({mocked} mock write(s); the rest hit Google Calendar.)"
    if fails:
        base += f" Some writes failed: {'; '.join(str(f) for f in fails[:3])}"
    return base


def _book_fail_reply(payload: dict) -> str:
    reason = payload.get("reason")
    body = payload.get("body")
    if reason is None and isinstance(body, dict):
        reason = body.get("detail")
    if reason is None:
        reason = body if body is not None else "unknown error"
    if isinstance(reason, dict):
        reason = reason.get("detail", str(reason))
    if payload.get("reason") == "no_active_proposal":
        return "There's no pending plan to book — say \"hatch a plan\" first, or tap through the Hatch UI."
    if str(payload.get("reason", "")).startswith("proposal_not_pending"):
        return "That plan isn't pending anymore (maybe already booked or skipped). Hatch a new one if you need to."
    return f"Booking didn't complete — {reason}."


@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage) -> None:
    text_parts: list[str] = []
    for part in msg.content:
        if isinstance(part, TextContent):
            text_parts.append(part.text)
    inbound = " ".join(text_parts).strip()
    # ASI:One often prefixes ``@agent1qfw...`` — that breaks ``\\bpropose`` if the
    # handle ends in a digit (``3propose``). Strip @tokens before routing.
    free_text = normalize_inbound(inbound)
    ctx.logger.info(
        f"ChatMessage from {sender} ({len(inbound)} chars): {inbound[:200]!r} "
        f"| normalized: {free_text[:200]!r}"
    )

    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id,
        ),
    )

    intent = classify_intent(inbound)
    reply = _CHITCHAT

    try:
        await health_check()
    except (httpx.ConnectError, httpx.ConnectTimeout):
        reply = _OFFLINE
        await _send_text(ctx, sender, reply)
        return
    except Exception as e:
        ctx.logger.warning(f"health_check failed: {e}")
        reply = _OFFLINE
        await _send_text(ctx, sender, reply)
        return

    try:
        if intent == "propose_pick":
            idx = parse_reactive_pick_index(inbound)
            if idx is None:
                reply = "Couldn't parse which option number you meant."
            else:
                st0 = await fetch_state()
                rmsg = _last_reactive_message(st0)
                matches = (rmsg or {}).get("matches") or []
                if not rmsg or not matches or idx > len(matches):
                    reply = _propose_pick_reply(st0, idx)
                else:
                    ev = matches[idx - 1]
                    eid = ev.get("id")
                    if not eid:
                        reply = "That option has no id — can't promote it. Try from the Hatch UI."
                    else:
                        users = st0.get("users") or []
                        uid = (os.environ.get("HATCH_PROXY_USER_ID") or "").strip() or (
                            users[0]["id"] if users else ""
                        )
                        if not uid:
                            reply = "No proxy user id — set HATCH_PROXY_USER_ID or seed users in /state."
                        else:
                            pr = await post_propose_idea(event_id=eid, user_id=uid)
                            if not pr.get("ok"):
                                reply = (
                                    f"Couldn't promote that idea ({pr.get('reason', pr)}). "
                                    "It may have fallen off the ideas panel — run another reactive ask."
                                )
                            else:
                                st1 = await fetch_state()
                                reply = _propose_pick_reply(st1, idx)

        elif intent == "reactive":
            st0 = await fetch_state()
            users = st0.get("users") or []
            uid = (os.environ.get("HATCH_PROXY_USER_ID") or "").strip() or (
                users[0]["id"] if users else ""
            )
            if not uid:
                reply = "No users in Hatch state — can't proxy your message into the group chat."
            else:
                sent = await post_send_message(user_id=uid, text=free_text)
                if not sent.get("ok"):
                    reply = f"Couldn't post to the Hatch API: {sent.get('reason', sent)}"
                else:
                    st1 = await fetch_state()
                    reply = _reactive_followup_reply(st1, free_text)

        elif intent == "propose":
            plan = await post_propose()
            if plan.get("ok"):
                state = await fetch_state()
                reply = _propose_ok_reply(state)
            else:
                reply = _propose_fail_reply(plan)

        elif intent == "book":
            result = await post_approve_all()
            if result.get("all_approved") and result.get("booking"):
                reply = _book_ok_reply(result)
            elif result.get("ok") is False or result.get("reason"):
                reply = _book_fail_reply(result)
            elif result.get("approved") and not result.get("all_approved"):
                reply = (
                    "Approved some votes but not everyone yet — open the Hatch UI "
                    "or ask me to \"book it\" again after the last person taps I'm in."
                )
            else:
                reply = _book_fail_reply(result)

        else:
            reply = _CHITCHAT

    except httpx.HTTPStatusError as e:
        ctx.logger.error(f"HTTP error: {e}")
        reply = f"Hatch API returned an error ({e.response.status_code}). Is the server running?"
    except Exception as e:
        ctx.logger.error(traceback.format_exc())
        reply = f"Hatch internal error: {e}"

    await _send_text(ctx, sender, reply)


async def _send_text(ctx: Context, sender: str, text: str) -> None:
    await ctx.send(
        sender,
        ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=text)],
        ),
    )


@chat_proto.on_message(ChatAcknowledgement)
async def handle_chat_ack(ctx: Context, sender: str, ack: ChatAcknowledgement) -> None:
    ctx.logger.info(f"ChatAcknowledgement from {sender} for msg_id={ack.acknowledged_msg_id}")


agent.include(chat_proto, publish_manifest=True)


if __name__ == "__main__":
    print("Hatch uAgent address:", agent.address)
    wallet_addr = agent.wallet.address() if callable(agent.wallet.address) else agent.wallet.address
    print("Wallet address (for Almanac contract registration):", wallet_addr)
    print("Network:", os.environ.get("HATCH_NETWORK", "mainnet"))
    print("Hatch API:", api_base_url())
    print("Starting agent loop (Ctrl+C to stop). Mailbox requires AGENTVERSE_API_KEY in .env.")
    agent.run()
