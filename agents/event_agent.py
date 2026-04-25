"""Event agent — queries events.json, ranks via matching.rank_events.

Absorbs the old Interest agent (interests are a JSON lookup, not a pipeline step).
"""
from __future__ import annotations

from datetime import datetime
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
from lib.matching import Window
from lib.protocol import EventRequest, EventResponse, RankedEvent

load_dotenv()

agent = Agent(
    name=agentverse.EVENT.name,
    seed=agentverse.EVENT.seed,
    mailbox=True,
    publish_agent_details=True,
)

chat_proto = Protocol(spec=chat_protocol_spec)


def handle(req: EventRequest) -> EventResponse:
    users = [u for u in matching.load_users() if u["id"] in req.user_ids]
    events = matching.load_events()
    windows = [
        Window(datetime.fromisoformat(w.start_iso), datetime.fromisoformat(w.end_iso))
        for w in req.windows
    ]
    ranked = matching.rank_events(events, users, windows)
    return EventResponse(
        ranked=[
            RankedEvent(
                id=e["id"],
                title=e["title"],
                datetime=e["datetime"],
                duration_minutes=e["duration_minutes"],
                location=e["location"],
                price=e["price"],
                url=e["url"],
                tags=e["tags"],
                score=e["_score"],
            )
            for e in ranked
        ]
    )


@chat_proto.on_message(ChatMessage)
async def on_message(ctx: Context, sender: str, msg: ChatMessage) -> None:
    text = " ".join(c.text for c in msg.content if isinstance(c, TextContent))
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id),
    )

    try:
        req = EventRequest.model_validate_json(text)
        payload = handle(req).model_dump_json()
    except Exception as e:
        ctx.logger.error(f"event agent error: {e}")
        payload = "Event agent: send a JSON EventRequest."

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
    print(f"event agent address: {agent.address}")
    agent.run()
