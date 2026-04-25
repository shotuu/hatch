"""AgentClient — typed request/response bridge to remote Chat Protocol agents.

Used by the orchestrator (and FastAPI handlers) to call out to Agentverse-hosted
agents without becoming an agent itself.

Usage:
    from lib.integrations.agent_client import client
    from lib.integrations import agentverse
    from lib.protocol import CalendarRequest, CalendarResponse

    resp = await client().request(
        agentverse.CALENDAR,
        CalendarRequest(...),
        CalendarResponse,
    )

How it works:
    A single in-process uAgent ("hatch-orchestrator-client") subscribes to
    Chat Protocol. Outgoing messages are sent via its Context. Incoming replies
    are matched back to a `(sender_address) -> Future` map and resolve the
    pending request. One in-flight request per remote address at a time.

Network delivery:
    The actual send is delegated to `_dispatch_send()` — there are two viable
    paths in the current uAgents ecosystem and they shift between versions.
    Pick one and verify against the docs you're using:

        a) `from uagents.communication import send_sync_message`
           One-shot send-and-await. Doesn't need a running local agent.

        b) Run the client agent in the same process (Bureau-style) and use
           `agent._ctx.send(...)`. More moving parts, more reliable for
           bidirectional Chat Protocol exchanges.

    The skeleton below picks (a) for simplicity. Swap in (b) if you need
    streaming or multiple replies per request.

References:
    https://innovationlab.fetch.ai/resources/docs/agent-communication/chat-protocol
    https://innovationlab.fetch.ai/resources/docs/agentverse
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import TypeVar
from uuid import uuid4

from dotenv import load_dotenv
from pydantic import BaseModel
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
)

from lib.integrations.agentverse import AgentInfo

load_dotenv()

T = TypeVar("T", bound=BaseModel)

CLIENT_SEED = os.environ.get(
    "CLIENT_AGENT_SEED", "hatch-orchestrator-client-seed-change-me"
)
DEFAULT_TIMEOUT = float(os.environ.get("AGENT_REQUEST_TIMEOUT", "15"))


class AgentClient:
    _instance: "AgentClient | None" = None

    def __init__(self) -> None:
        # one Future per (target_address) — assumes one in-flight per agent
        self._pending: dict[str, asyncio.Future] = {}

    @classmethod
    def get(cls) -> "AgentClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _build_chat(self, payload: BaseModel) -> ChatMessage:
        return ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=payload.model_dump_json())],
        )

    async def _dispatch_send(self, target_address: str, msg: ChatMessage) -> ChatMessage:
        """Send a ChatMessage to a remote agent and return the reply.

        Implementation is intentionally swappable. The skeleton uses the uagents
        send-sync helper; see module docstring for alternatives.
        """
        try:
            from uagents.communication import send_sync_message  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "Unable to import a uagents send helper. Pin a uagents version "
                "that exposes `uagents.communication.send_sync_message` or swap "
                "this method for the Bureau-based pattern."
            ) from e

        # Some uagents versions name params (destination=, response_type=) differently.
        # Adjust as needed when you wire this for real.
        return await send_sync_message(
            destination=target_address,
            message=msg,
            response_type=ChatMessage,
            timeout=DEFAULT_TIMEOUT,
        )

    async def request(
        self,
        target: AgentInfo,
        payload: BaseModel,
        response_type: type[T],
        *,
        timeout: float | None = None,
    ) -> T:
        if not target.address:
            raise RuntimeError(
                f"{target.name} has no address. Deploy the agent, then set "
                f"{target.address_env} in .env (or run scripts/print_addresses.py)."
            )

        msg = self._build_chat(payload)
        reply: ChatMessage = await asyncio.wait_for(
            self._dispatch_send(target.address, msg),
            timeout=timeout or DEFAULT_TIMEOUT,
        )
        text = " ".join(c.text for c in reply.content if isinstance(c, TextContent))
        return response_type.model_validate_json(text)


def client() -> AgentClient:
    return AgentClient.get()
