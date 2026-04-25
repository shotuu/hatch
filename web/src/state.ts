import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { Event, GroupSnapshot } from "./types";

export type Celebration = {
  id: string;
  text: string;
  eventTitle: string;
  ts: string;
};

const POLL_MS = 1000;

const EMPTY: GroupSnapshot = {
  messages: [],
  current_proposal: null,
  nest_warmth: 6,
  nest_max: 30,
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
    nest_warmth: typeof o.nest_warmth === "number" ? o.nest_warmth : EMPTY.nest_warmth,
    nest_max: typeof o.nest_max === "number" ? o.nest_max : EMPTY.nest_max,
    last_booking: o.last_booking ?? null,
    ideas: Array.isArray(o.ideas) ? (o.ideas as GroupSnapshot["ideas"]) : [],
    users: Array.isArray(o.users) ? (o.users as GroupSnapshot["users"]) : [],
  };
}

export function useGroupState() {
  const [snapshot, setSnapshot] = useState<GroupSnapshot>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [wipeStatus, setWipeStatus] = useState<string | null>(null);
  const [plannedEvents, setPlannedEvents] = useState<Event[]>([]);
  const [celebrations, setCelebrations] = useState<Celebration[]>([]);
  const [reactiveSkips, setReactiveSkips] = useState<Record<string, string[]>>({});
  const [rejectedEventIds, setRejectedEventIds] = useState<Set<string>>(new Set());
  const [resolvedReactives, setResolvedReactives] = useState<Set<string>>(new Set());
  const stopRef = useRef(false);
  const seenBookedRef = useRef<Set<string>>(new Set());

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

  // Watch for proposal transition into "booked" — capture as planned, then
  // auto-dismiss the active proposal. The hatched-plan notification itself is
  // now a backend timeline message so every phone sees it in the same place.
  useEffect(() => {
    const p = snapshot.current_proposal;
    if (!p || p.status !== "booked") return;
    if (seenBookedRef.current.has(p.id)) return;
    seenBookedRef.current.add(p.id);

    setPlannedEvents((prev) => [
      p.event,
      ...prev.filter((e) => e.id !== p.event.id),
    ]);
    // Remove from "Ideas in the air" — no longer being considered.
    api.dismissIdea(p.event.id).catch(() => {});

    const id = setTimeout(() => {
      api.dismissProposal().catch(() => {});
    }, 3500);
    return () => clearTimeout(id);
  }, [snapshot.current_proposal?.id, snapshot.current_proposal?.status]);

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
  const dismissProposal = wrap(async () => {
    const evtId = snapshot.current_proposal?.event.id;
    await api.dismissProposal();
    if (evtId) await api.dismissIdea(evtId).catch(() => {});
  });
  const swapAlternate = wrap(() => api.swapAlternate());
  const dismissIdea = wrap((eventId: string) => api.dismissIdea(eventId));
  const proposeIdea = wrap((eventId: string, userId?: string) =>
    api.proposeIdea(eventId, userId)
  );

  // Mark a reactive reply as "resolved" — i.e. one of its options got proposed
  // to the group, so it shouldn't be re-pinned even if the resulting proposal
  // is later dismissed.
  const proposeReactiveOption = (
    eventId: string,
    reactiveId: string,
    userId: string,
  ) => {
    setResolvedReactives((prev) => {
      if (prev.has(reactiveId)) return prev;
      const next = new Set(prev);
      next.add(reactiveId);
      return next;
    });
    return proposeIdea(eventId, userId);
  };

  const skipReactiveOption = useCallback(
    (eventId: string, userId: string) => {
      setRejectedEventIds((prev) => {
        if (prev.has(eventId)) return prev;
        const next = new Set(prev);
        next.add(eventId);
        return next;
      });
      setReactiveSkips((prev) => {
        const current = prev[eventId] || [];
        if (current.includes(userId)) return prev;
        return { ...prev, [eventId]: [...current, userId] };
      });
      api.dismissIdea(eventId).catch(() => {});
    },
    [],
  );
  const skipProposal = wrap(async (userId: string) => {
    const evtId = snapshot.current_proposal?.event.id;
    if (evtId) {
      setRejectedEventIds((prev) => {
        if (prev.has(evtId)) return prev;
        const next = new Set(prev);
        next.add(evtId);
        return next;
      });
      setReactiveSkips((prev) => {
        const current = prev[evtId] || [];
        if (current.includes(userId)) return prev;
        return { ...prev, [evtId]: [...current, userId] };
      });
    }
    setSnapshot((prev) => ({ ...prev, current_proposal: null }));
    await api.dismissProposal();
    if (evtId) await api.dismissIdea(evtId).catch(() => {});
  });
  const reset = wrap(async () => {
    await api.reset();
    seenBookedRef.current = new Set();
    setPlannedEvents([]);
    setCelebrations([]);
    setReactiveSkips({});
    setRejectedEventIds(new Set());
    setResolvedReactives(new Set());
  });
  const setWarmth = wrap((days: number) => {
    // Guard against NaN / undefined (e.g. before first /state poll resolves) —
    // those serialize to null and the backend rejects with 422.
    const safe = Number.isFinite(days) ? Math.max(0, Math.round(days)) : 0;
    return api.setWarmth(safe);
  });

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
    plannedEvents,
    celebrations,
    reactiveSkips,
    rejectedEventIds,
    resolvedReactives,
    send,
    triggerProactive,
    approve,
    dismissProposal,
    skipProposal,
    swapAlternate,
    dismissIdea,
    proposeIdea,
    proposeReactiveOption,
    skipReactiveOption,
    reset,
    setWarmth,
    onWipe,
    demoLakers,
  };
}

export type GroupActions = ReturnType<typeof useGroupState>;
