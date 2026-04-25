"""Calendar agent — stub. Wraps lib.integrations.google_calendar.freebusy behind Chat Protocol.

Build this after proposer_agent is confirmed working on Agentverse.
Pattern: copy proposer_agent.py, swap the handler to call lib.matching.find_overlap.
"""
from __future__ import annotations

from dotenv import load_dotenv
from uagents import Agent, Protocol
from uagents_core.contrib.protocols.chat import chat_protocol_spec

from lib.integrations import agentverse

load_dotenv()

agent = Agent(
    name=agentverse.CALENDAR.name,
    seed=agentverse.CALENDAR.seed,
    mailbox=True,
    publish_agent_details=True,
)
chat_proto = Protocol(spec=chat_protocol_spec)
agent.include(chat_proto, publish_manifest=True)


if __name__ == "__main__":
    print(f"calendar agent address: {agent.address}")
    agent.run()
