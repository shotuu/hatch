"""Event agent — stub. Queries events.json, ranks via lib.matching.rank_events.

Absorbs the old Interest agent (interests are a JSON lookup, not a pipeline step).
"""
from __future__ import annotations

from dotenv import load_dotenv
from uagents import Agent, Protocol
from uagents_core.contrib.protocols.chat import chat_protocol_spec

from lib.integrations import agentverse

load_dotenv()

agent = Agent(
    name=agentverse.EVENT.name,
    seed=agentverse.EVENT.seed,
    mailbox=True,
    publish_agent_details=True,
)
chat_proto = Protocol(spec=chat_protocol_spec)
agent.include(chat_proto, publish_manifest=True)


if __name__ == "__main__":
    print(f"event agent address: {agent.address}")
    agent.run()
