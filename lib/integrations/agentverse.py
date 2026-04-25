"""Agentverse helpers — agent address registry, manifest publishing tips.

Set the addresses in .env once each agent is deployed; read them here so the
orchestrator and any cross-agent calls stay in one place.

Deploy guide:
  https://innovationlab.fetch.ai/resources/docs/agentverse/deploy-agent-on-agentverse-via-render
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentInfo:
    name: str
    seed_env: str
    address_env: str  # set after deployment so other agents/clients can reach it

    @property
    def seed(self) -> str:
        return os.environ.get(self.seed_env, f"{self.name}-seed-change-me")

    @property
    def address(self) -> str | None:
        return os.environ.get(self.address_env)


PROPOSER = AgentInfo(
    name="hatch-proposer",
    seed_env="PROPOSER_AGENT_SEED",
    address_env="PROPOSER_AGENT_ADDRESS",
)
CALENDAR = AgentInfo(
    name="hatch-calendar",
    seed_env="CALENDAR_AGENT_SEED",
    address_env="CALENDAR_AGENT_ADDRESS",
)
EVENT = AgentInfo(
    name="hatch-event",
    seed_env="EVENT_AGENT_SEED",
    address_env="EVENT_AGENT_ADDRESS",
)
BOOKING = AgentInfo(
    name="hatch-booking",
    seed_env="BOOKING_AGENT_SEED",
    address_env="BOOKING_AGENT_ADDRESS",
)


def all_agents() -> list[AgentInfo]:
    return [PROPOSER, CALENDAR, EVENT, BOOKING]
