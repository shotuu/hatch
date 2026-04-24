"""Booking agent — stub. Writes the event to all 4 Google Calendars, then confirms.

On success: resets the group's expiry timer and posts the "Done" message.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv
from uagents import Agent, Protocol
from uagents_core.contrib.protocols.chat import chat_protocol_spec

load_dotenv()

agent = Agent(
    name="plans-booking",
    seed=os.environ.get("BOOKING_AGENT_SEED", "plans-booking-seed-change-me"),
    mailbox=True,
    publish_agent_details=True,
)
chat_proto = Protocol(spec=chat_protocol_spec)
agent.include(chat_proto, publish_manifest=True)


if __name__ == "__main__":
    print(f"booking agent address: {agent.address}")
    agent.run()
