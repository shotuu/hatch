"""Hatch orchestrator uAgent — minimal Chat Protocol stub for ASI:One / Agentverse.

This file does three things only (Phase 2 gate):
  1. Create a uAgent with a stable identity (seed → address).
  2. Attach the official Fetch **Chat Protocol** spec so ASI:One and other clients
     speak the same message shapes (manifests register on Almanac).
  3. Reply with a **hardcoded** text payload — no LangGraph / LLM / Calendar yet.

Docs:
  Chat Protocol overview:
    https://innovationlab.fetch.ai/resources/docs/agent-communication/chat-protocol
  uAgents Chat Protocol guide:
    https://uagents.fetch.ai/docs/guides/chat_protocol
  Deploy (mailbox) example:
    https://innovationlab.fetch.ai/resources/docs/agentverse/deploy-agent-on-agentverse-via-render

Run locally:
  python -m agents.agentverse.main
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

# Load AGENT_SEED_PHRASE, AGENTVERSE_API_KEY, etc. from a local .env file.
load_dotenv()

# ---------------------------------------------------------------------------
# 1) uAgent identity
# ---------------------------------------------------------------------------
# `name` is a human-readable label in logs and Agentverse UI.
# `seed` must be a **stable secret string** in production: the same seed always
# yields the same agent address, which is how you update code without losing
# your Agentverse registration. CLAUDE.md calls this AGENT_SEED_PHRASE.
#
# `mailbox=True` routes inbound traffic through Fetch's hosted mailbox service
# instead of requiring a public IP on your laptop — required for ASI:One and
# Agentverse to reach the agent while you develop locally or on Render.
#
# `publish_agent_details=True` publishes metadata (name, readme, protocols) so
# the agent can be discovered and invoked via the ecosystem tooling.
agent = Agent(
    name=os.environ.get("HATCH_UAGENT_NAME", "hatch-main"),
    seed=os.environ.get("AGENT_SEED_PHRASE", "hatch-main-dev-seed-change-me"),
    # Optional: "testnet" makes Almanac contract registration easier during dev
    # (you can fund via faucet instead of mainnet tokens).
    network=os.environ.get("HATCH_NETWORK", "mainnet"),
    # The Local Agent Inspector expects a local HTTP endpoint it can probe.
    # uAgents receives inbound envelopes at POST /submit by default.
    port=int(os.environ.get("HATCH_UAGENT_PORT", "8000")),
    mailbox=True,
    publish_agent_details=True,
)

# ---------------------------------------------------------------------------
# 2) Chat Protocol wiring
# ---------------------------------------------------------------------------
# `chat_protocol_spec` is the canonical protocol definition from uagents-core.
# Wrapping it in `Protocol(spec=...)` registers the correct digest / manifest so
# external clients (including ASI:One) negotiate the same request/response models.
chat_proto = Protocol(spec=chat_protocol_spec)

# Fixed copy for Phase 1 — swap this for LangGraph output once the pipeline exists.
HATCH_HANDSHAKE_REPLY = (
    "Hatch is online — plans, hatched. "
    "This is a Chat Protocol handshake: ASI:One can reach me. "
    "Orchestration (calendar → events → proposal → book) comes next."
)


@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage) -> None:
    """Handle an inbound conversational turn.

    Chat Protocol flow (simplified):
      - Peers send `ChatMessage` with one or more typed `content` parts.
      - We should send `ChatAcknowledgement` so the sender knows we accepted it.
      - We respond with another `ChatMessage` (often `TextContent`).

    `sender` is the other party's agent address (ASI:One / bridge / user agent).
    """
    # Extract plain text from structured parts (ASI:One typically sends `text`).
    text_parts: list[str] = []
    for part in msg.content:
        if isinstance(part, TextContent):
            text_parts.append(part.text)
    inbound = " ".join(text_parts).strip()
    ctx.logger.info(
        f"ChatMessage from {sender} ({len(inbound)} chars): {inbound[:200]!r}"
    )

    # Protocol courtesy: acknowledge the exact message id we received.
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id,
        ),
    )

    # Phase-1 behavior: ignore LLM parsing and always return the canned reply.
    await ctx.send(
        sender,
        ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=HATCH_HANDSHAKE_REPLY)],
        ),
    )


@chat_proto.on_message(ChatAcknowledgement)
async def handle_chat_ack(ctx: Context, sender: str, ack: ChatAcknowledgement) -> None:
    """Inbound acks from the peer — log only; no reply (avoids ack loops)."""
    ctx.logger.info(f"ChatAcknowledgement from {sender} for msg_id={ack.acknowledged_msg_id}")


# Attach protocol to the agent and publish its manifest for discovery / ASI:One.
agent.include(chat_proto, publish_manifest=True)


if __name__ == "__main__":
    # Print once so you can paste the address into Agentverse UI or ASI:One.
    print("Hatch uAgent address:", agent.address)
    # `LocalWallet.address` is a method in some uAgents versions.
    wallet_addr = agent.wallet.address() if callable(agent.wallet.address) else agent.wallet.address
    print("Wallet address (for Almanac contract registration):", wallet_addr)
    print("Network:", os.environ.get("HATCH_NETWORK", "mainnet"))
    print("Starting agent loop (Ctrl+C to stop). Mailbox requires AGENTVERSE_API_KEY in .env.")
    agent.run()
