"""Proposer agent — composes the in-chat suggestion in a natural friend-voice.

Chat Protocol reference:
  https://innovationlab.fetch.ai/resources/docs/agent-communication/chat-protocol

Run locally for dev:
  python -m agents.proposer_agent

Deploy to Agentverse: follow the Render example, then paste the agent address
into ASI:One so judges can discover it.
  https://innovationlab.fetch.ai/resources/docs/agentverse/deploy-agent-on-agentverse-via-render
"""
from __future__ import annotations

import os
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

from lib import asi_client

load_dotenv()

SEED = os.environ.get("PROPOSER_AGENT_SEED", "plans-proposer-seed-change-me")

agent = Agent(
    name="plans-proposer",
    seed=SEED,
    mailbox=True,
    publish_agent_details=True,
)

chat_proto = Protocol(spec=chat_protocol_spec)

SYSTEM_PROMPT = (
    "You are the Plans proposer agent. You live inside a friend group chat. "
    "The group has been silent for weeks and the chat is about to expire. "
    "Given a free-time window and a candidate event, write ONE short message "
    "(max 2 sentences) in a casual friend voice that:\n"
    "1. names the time window,\n"
    "2. proposes the event,\n"
    "3. ends with a soft CTA like 'want me to set it up?'\n"
    "No emojis. No exclamation marks. Don't sound like a salesperson."
)


def compose_proposal(window_text: str, event: dict) -> str:
    user = (
        f"Window: {window_text}\n"
        f"Event: {event['title']} at {event['location']}, "
        f"{event['datetime']}, ${event['price']}."
    )
    return asi_client.chat(SYSTEM_PROMPT, user, temperature=0.6, max_tokens=160)


@chat_proto.on_message(ChatMessage)
async def on_message(ctx: Context, sender: str, msg: ChatMessage) -> None:
    text = " ".join(c.text for c in msg.content if isinstance(c, TextContent))
    ctx.logger.info(f"recv from {sender}: {text!r}")

    # Acknowledge receipt (required by Chat Protocol).
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.utcnow(),
            acknowledged_msg_id=msg.msg_id,
        ),
    )

    # For now, echo a canned proposal. Orchestrator will pass structured context later.
    reply_text = (
        "You're all free Saturday 2–6pm. There's a free gallery opening in the "
        "Arts District at 3pm — want me to set it up?"
    )

    await ctx.send(
        sender,
        ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=reply_text)],
        ),
    )


@chat_proto.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, ack: ChatAcknowledgement) -> None:
    ctx.logger.info(f"ack from {sender} for {ack.acknowledged_msg_id}")


agent.include(chat_proto, publish_manifest=True)


if __name__ == "__main__":
    print(f"proposer agent address: {agent.address}")
    agent.run()
