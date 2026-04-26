"""Async HTTP client for the Hatch FastAPI server (Phase 7).

The uAgent runs in a separate process from `server.py`. It reaches the same
LangGraph-backed state the web UI uses by calling localhost HTTP endpoints.

Env:
  HATCH_API_BASE_URL — optional full base, e.g. http://127.0.0.1:8005
  If unset: http://{HATCH_API_HOST}:{SERVER_PORT}
    - HATCH_API_HOST defaults to 127.0.0.1 (do NOT use SERVER_HOST=0.0.0.0 for
      outbound requests — that is a bind address, not a connect target).
    - SERVER_PORT defaults to 8005 (match server.py default).
"""

from __future__ import annotations

import os
from typing import Any

import httpx


def api_base_url() -> str:
    explicit = os.environ.get("HATCH_API_BASE_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    host = os.environ.get("HATCH_API_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = int(os.environ.get("SERVER_PORT", "8005"))
    return f"http://{host}:{port}"


async def health_check() -> dict[str, Any]:
    base = api_base_url()
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(f"{base}/health")
        r.raise_for_status()
        return r.json()


async def fetch_state() -> dict[str, Any]:
    base = api_base_url()
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{base}/state")
        r.raise_for_status()
        return r.json()


async def post_send_message(*, user_id: str, text: str) -> dict[str, Any]:
    """Post as a group member — runs the reactive LangGraph pipeline in server."""
    base = api_base_url()
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            f"{base}/send_message",
            json={"user_id": user_id, "text": text},
        )
        try:
            body = r.json()
        except Exception:
            body = {"ok": False, "raw": r.text}
        if r.status_code >= 400:
            detail = body.get("detail") if isinstance(body, dict) else str(body)
            return {"ok": False, "http_status": r.status_code, "reason": detail}
        return body if isinstance(body, dict) else {"ok": True}


async def post_propose_idea(*, event_id: str, user_id: str) -> dict[str, Any]:
    """Promote a panel idea to the pinned proposal (same as UI Propose to group)."""
    base = api_base_url()
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{base}/propose_idea",
            json={"event_id": event_id, "user_id": user_id},
        )
        try:
            body = r.json()
        except Exception:
            body = {"ok": False, "raw": r.text}
        if r.status_code >= 400:
            detail = body.get("detail") if isinstance(body, dict) else str(body)
            return {"ok": False, "http_status": r.status_code, "reason": detail}
        return body if isinstance(body, dict) else {"ok": True}


async def post_propose() -> dict[str, Any]:
    """Run proposal pipeline; returns server JSON (ok or error shape)."""
    base = api_base_url()
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{base}/propose")
        return r.json()


async def post_approve_all() -> dict[str, Any]:
    """Approve on behalf of every user in the pending proposal until booked.

    Each POST /approve is idempotent for users already marked in. The last
    approval triggers `book_plan` inside the server.
    """
    base = api_base_url()
    async with httpx.AsyncClient(timeout=180.0) as client:
        r0 = await client.get(f"{base}/state")
        r0.raise_for_status()
        st = r0.json()
        p = st.get("current_proposal")
        if not p:
            return {"ok": False, "reason": "no_active_proposal"}
        if p.get("status") != "pending":
            return {
                "ok": False,
                "reason": f"proposal_not_pending:{p.get('status')}",
            }
        approvals = p.get("approvals") or {}
        uids = list(approvals.keys())
        if not uids:
            return {"ok": False, "reason": "no_approval_slots"}

        last: dict[str, Any] = {}
        for uid in uids:
            r = await client.post(f"{base}/approve", json={"user_id": uid})
            try:
                last = r.json()
            except Exception:
                last = {"ok": False, "raw": r.text}
            if r.status_code >= 400:
                detail = last.get("detail") if isinstance(last, dict) else str(last)
                return {
                    "ok": False,
                    "http_status": r.status_code,
                    "body": last,
                    "reason": detail,
                }
            if last.get("all_approved"):
                return last
        return last
