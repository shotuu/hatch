"""Print deterministic Agentverse addresses for each agent seed in .env.

Paste the output into .env so the orchestrator can talk to the deployed agents.

Usage:
    python -m scripts.print_addresses
"""
from __future__ import annotations

from dotenv import load_dotenv
from uagents import Agent

from lib.integrations import agentverse

load_dotenv()


def main() -> None:
    print("# Paste these into .env after deploying each agent.")
    print()
    for info in agentverse.all_agents():
        a = Agent(name=info.name, seed=info.seed)
        print(f"{info.address_env}={a.address}")


if __name__ == "__main__":
    main()
