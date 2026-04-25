"""Booking agent — writes the event to all N Google Calendars, then confirms.

Note: if hosted on Agentverse the agent needs the OAuth tokens to be reachable.
For the hackathon demo, prefer running this agent locally OR keep booking in
the local orchestrator path and treat this agent as a Chat-Protocol shell for
prize compliance only.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

from lib import matching
from lib.integrations import agentverse
from lib.protocol import BookingRequest, BookingResponse

load_dotenv()

agent = Agent(
    name=agentverse.BOOKING.name,
    seed=agentverse.BOOKING.seed,
    mailbox=True,
    publish_agent_details=True,
)

chat_proto = Protocol(spec=chat_protocol_spec)


def handle(req: BookingRequest) -> BookingResponse:
    events = {e["id"]: e for e in matching.load_events()}
    event = events.get(req.event_id)
    if not event:
        return BookingResponse(ok=False, error=f"unknown event: {req.event_id}")

    users = {u["id"]: u for u in matching.load_users()}
    selected = [users[uid] for uid in req.user_ids if uid in users]
    start = datetime.fromisoformat(event["datetime"])
    end = start + timedelta(minutes=event["duration_minutes"])
    repo_root = Path(__file__).resolve().parent.parent

    written = 0
    try:
        from lib.integrations import google_calendar
    except Exception as e:
        return BookingResponse(ok=False, error=f"google_calendar import failed: {e}")

    for u in selected:
        token_path = repo_root / u["google_token_path"]
        if not token_path.exists():
            continue
        try:
            google_calendar.insert_event(
                u["google_token_path"],
                summary=f"Hatch · {event['title']}",
                location=event["location"],
                description=f"Hatched by your group chat.\n{event['url']}",
                start=start,
                end=end,
            )
            written += 1
        except Exception as e:
            # keep going — partial booking is still progress
            print(f"booking failed for {u['id']}: {e}")

    return BookingResponse(ok=written > 0, calendars_written=written)


@chat_proto.on_message(ChatMessage)
async def on_message(ctx: Context, sender: str, msg: ChatMessage) -> None:
    text = " ".join(c.text for c in msg.content if isinstance(c, TextContent))
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id),
    )

    try:
        req = BookingRequest.model_validate_json(text)
        payload = handle(req).model_dump_json()
    except Exception as e:
        ctx.logger.error(f"booking agent error: {e}")
        payload = "Booking agent: send a JSON BookingRequest."

    await ctx.send(
        sender,
        ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=payload)],
        ),
    )


@chat_proto.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, ack: ChatAcknowledgement) -> None:
    pass


agent.include(chat_proto, publish_manifest=True)


if __name__ == "__main__":
    print(f"booking agent address: {agent.address}")
    agent.run()
