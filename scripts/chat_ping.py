"""Minimal Chat Protocol ping client for local testing.

Use this when the Agentverse Local Inspector UI can't connect to localhost.
It proves your `ChatMessage` handler works by sending a message from a second
local uAgent to a target agent address and logging the response.

Run:
  # terminal 1
  python -m agents.agentverse.main

  # terminal 2 (new shell)
  python -m scripts.chat_ping agent1...
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from uagents import Agent, Context, Model
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent

load_dotenv()


class Args(Model):
    """CLI args (kept as Model so uAgents logs are consistent)."""

    target: str


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: python -m scripts.chat_ping <target_agent_address>")
        raise SystemExit(2)

    target = sys.argv[1].strip()

    # Separate local agent identity; fixed seed is fine for dev.
    client = Agent(name="hatch-chat-ping", seed="hatch-chat-ping-dev-seed", port=8010)

    @client.on_event("startup")
    async def on_startup(ctx: Context) -> None:
        ctx.logger.info("Sending ChatMessage to %s", target)
        await ctx.send(
            target,
            ChatMessage(
                timestamp=datetime.now(timezone.utc),
                msg_id=uuid4(),
                content=[TextContent(type="text", text="ping")],
            ),
        )

    @client.on_message(ChatMessage)
    async def on_reply(ctx: Context, sender: str, msg: ChatMessage) -> None:
        text = " ".join(c.text for c in msg.content if isinstance(c, TextContent))
        print(f"reply from {sender}: {text}")
        ctx.logger.info("Done; stopping client.")
        raise SystemExit(0)

    client.run()


if __name__ == "__main__":
    main()

