import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { GroupSnapshot } from "./types";

const POLL_MS = 1000;

const EMPTY: GroupSnapshot = {
  messages: [],
  current_proposal: null,
  expiry_days: 6,
  last_booking: null,
  ideas: [],
  users: [],
};

/** If `/api/state` hits the wrong process (e.g. uAgent on :8000), JSON may lack `users` and crash React. */
function normalizeSnapshot(raw: unknown): GroupSnapshot {
  if (!raw || typeof raw !== "object") return EMPTY;
  const o = raw as Record<string, unknown>;
  return {
    messages: Array.isArray(o.messages) ? (o.messages as GroupSnapshot["messages"]) : [],
    current_proposal:
      o.current_proposal === null || o.current_proposal === undefined
        ? null
        : (o.current_proposal as GroupSnapshot["current_proposal"]),
    expiry_days: typeof o.expiry_days === "number" ? o.expiry_days : EMPTY.expiry_days,
    last_booking: o.last_booking ?? null,
    ideas: Array.isArray(o.ideas) ? (o.ideas as GroupSnapshot["ideas"]) : [],
    users: Array.isArray(o.users) ? (o.users as GroupSnapshot["users"]) : [],
  };
}

export function useGroupState() {
  const [snapshot, setSnapshot] = useState<GroupSnapshot>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [wipeStatus, setWipeStatus] = useState<string | null>(null);
  const stopRef = useRef(false);

  // Polling loop
  useEffect(() => {
    stopRef.current = false;
    let timer: ReturnType<typeof setTimeout>;
    const tick = async () => {
      if (stopRef.current) return;
      try {
        const s = normalizeSnapshot(await api.state());
        setSnapshot(s);
      } catch {
        // ignore — server might be restarting
      }
      timer = setTimeout(tick, POLL_MS);
    };
    tick();
    return () => {
      stopRef.current = true;
      clearTimeout(timer!);
    };
  }, []);

  // ─── action wrappers ───
  const wrap = useCallback(<T extends any[]>(fn: (...a: T) => Promise<any>) => {
    return async (...args: T) => {
      setBusy(true);
      try {
        await fn(...args);
        // bump immediately for snappier UI
        const s = normalizeSnapshot(await api.state());
        setSnapshot(s);
      } finally {
        setBusy(false);
      }
    };
  }, []);

  const send = wrap((userId: string, text: string) => api.sendMessage(userId, text));
  const triggerProactive = wrap(() => api.propose());
  const approve = wrap((userId: string) => api.approve(userId));
  const dismissProposal = wrap(() => api.dismissProposal());
  const swapAlternate = wrap(() => api.swapAlternate());
  const dismissIdea = wrap((eventId: string) => api.dismissIdea(eventId));
  const proposeIdea = wrap((eventId: string) => api.proposeIdea(eventId));
  const reset = wrap(() => api.reset());

  const onWipe = async () => {
    setBusy(true);
    setWipeStatus("wiping…");
    try {
      const r = await api.wipe();
      setWipeStatus(`wiped ${r.total_deleted}`);
    } catch {
      setWipeStatus("failed");
    } finally {
      setBusy(false);
      setTimeout(() => setWipeStatus(null), 3000);
    }
  };

  // Demo helper: send Jono's Lakers msg
  const demoLakers = wrap(() =>
    api.sendMessage("jono", "anyone down for the Lakers game next week?")
  );

  return {
    snapshot,
    busy,
    wipeStatus,
    send,
    triggerProactive,
    approve,
    dismissProposal,
    swapAlternate,
    dismissIdea,
    proposeIdea,
    reset,
    onWipe,
    demoLakers,
  };
}

export type GroupActions = ReturnType<typeof useGroupState>;
