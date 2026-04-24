"""Calendar agent — stub. Wraps lib.calendar_client.freebusy behind Chat Protocol.

Build this after proposer_agent is confirmed working on Agentverse.
Pattern: copy proposer_agent.py, swap the handler to call lib.matching.find_overlap.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv
from uagents import Agent, Protocol
from uagents_core.contrib.protocols.chat import chat_protocol_spec

load_dotenv()

agent = Agent(
    name="plans-calendar",
    seed=os.environ.get("CALENDAR_AGENT_SEED", "plans-calendar-seed-change-me"),
    mailbox=True,
    publish_agent_details=True,
)
chat_proto = Protocol(spec=chat_protocol_spec)
agent.include(chat_proto, publish_manifest=True)


if __name__ == "__main__":
    print(f"calendar agent address: {agent.address}")
    agent.run()
