"""Proposer agent — composes the in-chat suggestion in a natural friend-voice.

Chat Protocol reference:
  https://innovationlab.fetch.ai/resources/docs/agent-communication/chat-protocol

Run locally for dev:
  python -m agents.proposer_agent

Deploy to Agentverse: follow the Render example, then paste the agent address
into .env (PROPOSER_AGENT_ADDRESS=agent1q...) and into ASI:One for discovery.
  https://innovationlab.fetch.ai/resources/docs/agentverse/deploy-agent-on-agentverse-via-render
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

from lib.integrations import agentverse, asi_one
from lib.protocol import ProposerRequest, ProposerResponse

load_dotenv()

agent = Agent(
    name=agentverse.PROPOSER.name,
    seed=agentverse.PROPOSER.seed,
    mailbox=True,
    publish_agent_details=True,
)

chat_proto = Protocol(spec=chat_protocol_spec)

SYSTEM_PROMPT = (
    "You are Hatch — the proposer agent that lives inside a friend group chat. "
    "The group has been silent for weeks and the chat is about to expire. "
    "Given a free-time window and a candidate event, write ONE short message "
    "(max 2 sentences) in a warm, casual friend voice that:\n"
    "1. names the time window,\n"
    "2. proposes the event,\n"
    "3. ends with a soft CTA like 'want me to set it up?'\n"
    "No emojis. No exclamation marks. Don't sound like a salesperson."
)


def compose_proposal(req: ProposerRequest) -> str:
    user = (
        f"Window: {req.window.start_iso} to {req.window.end_iso}\n"
        f"Event: {req.event.title} at {req.event.location}, "
        f"{req.event.datetime}, ${req.event.price}.\n"
        f"Group: {', '.join(req.user_names)}."
    )
    return asi_one.chat(SYSTEM_PROMPT, user, temperature=0.6, max_tokens=160)


async def _ack(ctx: Context, sender: str, msg_id) -> None:
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg_id),
    )


@chat_proto.on_message(ChatMessage)
async def on_message(ctx: Context, sender: str, msg: ChatMessage) -> None:
    text = " ".join(c.text for c in msg.content if isinstance(c, TextContent))
    ctx.logger.info(f"recv from {sender}: {text[:120]}")
    await _ack(ctx, sender, msg.msg_id)

    # Try typed request first; fall back to a friendly canned reply for ASI:One discovery.
    try:
        req = ProposerRequest.model_validate_json(text)
        try:
            reply_text = compose_proposal(req)
        except Exception as e:
            ctx.logger.error(f"ASI:One failed: {e}")
            reply_text = (
                f"You're free {req.window.start_iso[:10]}. "
                f"{req.event.title} at {req.event.location} — want me to set it up?"
            )
        payload = ProposerResponse(text=reply_text).model_dump_json()
    except Exception:
        payload = (
            "Hi! I'm Hatch — the proposer agent. Send me a JSON ProposerRequest "
            "and I'll compose a group-chat suggestion."
        )

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
    ctx.logger.info(f"ack from {sender} for {ack.acknowledged_msg_id}")


agent.include(chat_proto, publish_manifest=True)


if __name__ == "__main__":
    print(f"proposer agent address: {agent.address}")
    agent.run()
