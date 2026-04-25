"""Calendar agent — wraps lib.integrations.google_calendar.freebusy + matching.find_overlap."""
from __future__ import annotations

from datetime import datetime
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
from lib.protocol import CalendarRequest, CalendarResponse, FreeWindow

load_dotenv()

agent = Agent(
    name=agentverse.CALENDAR.name,
    seed=agentverse.CALENDAR.seed,
    mailbox=True,
    publish_agent_details=True,
)

chat_proto = Protocol(spec=chat_protocol_spec)


def handle(req: CalendarRequest) -> CalendarResponse:
    users = {u["id"]: u for u in matching.load_users()}
    selected = [users[uid] for uid in req.user_ids if uid in users]
    start = datetime.fromisoformat(req.search_start_iso)
    end = datetime.fromisoformat(req.search_end_iso)

    token_paths = {
        u["id"]: u["google_token_path"]
        for u in selected
        if (Path(__file__).resolve().parent.parent / u["google_token_path"]).exists()
    }

    busy: dict = {}
    if token_paths and len(token_paths) == len(selected):
        try:
            from lib.integrations import google_calendar
            busy = google_calendar.freebusy(token_paths, start, end)
        except Exception:
            busy = {u["id"]: [] for u in selected}
    else:
        busy = {u["id"]: [] for u in selected}

    windows = matching.find_overlap(busy, start, end, min_minutes=req.min_window_minutes)
    return CalendarResponse(
        windows=[FreeWindow(start_iso=w.start.isoformat(), end_iso=w.end.isoformat()) for w in windows]
    )


@chat_proto.on_message(ChatMessage)
async def on_message(ctx: Context, sender: str, msg: ChatMessage) -> None:
    text = " ".join(c.text for c in msg.content if isinstance(c, TextContent))
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id),
    )

    try:
        req = CalendarRequest.model_validate_json(text)
        payload = handle(req).model_dump_json()
    except Exception as e:
        ctx.logger.error(f"calendar agent error: {e}")
        payload = "Calendar agent: send a JSON CalendarRequest."

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
    print(f"calendar agent address: {agent.address}")
    agent.run()
