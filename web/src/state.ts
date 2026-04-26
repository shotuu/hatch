import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { Event, GroupSnapshot } from "./types";

export type Celebration = {
  id: string;
  text: string;
  eventTitle: string;
  ts: string;
};

export type CalendarFixtureStatus = {
  ok: boolean;
  ready: boolean;
  expected_total: number;
  actual_total: number;
  users: Array<{
    id: string;
    name: string;
    ready: boolean;
    expected_count: number;
    actual_count: number;
    issues: string[];
  }>;
};

const POLL_MS = 1000;
const CALENDAR_FIXTURE_POLL_MS = 10000;

const EMPTY: GroupSnapshot = {
  messages: [],
  current_proposal: null,
  nest_warmth: 6,
  nest_max: 30,
  last_booking: null,
  ideas: [],
  hatch_typing: false,
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
    hatch_typing: typeof o.hatch_typing === "boolean" ? o.hatch_typing : false,
    users: Array.isArray(o.users) ? (o.users as GroupSnapshot["users"]) : [],
  };
}

export function useGroupState() {
  const [snapshot, setSnapshot] = useState<GroupSnapshot>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [wipeStatus, setWipeStatus] = useState<string | null>(null);
  const [calendarFixtureStatus, setCalendarFixtureStatus] =
    useState<CalendarFixtureStatus | null>(null);
  const [calendarFixtureBusy, setCalendarFixtureBusy] = useState(false);
  const [calendarFixtureMessage, setCalendarFixtureMessage] = useState<string | null>(null);
  const [plannedEvents, setPlannedEvents] = useState<Event[]>([]);
  const [celebrations, setCelebrations] = useState<Celebration[]>([]);
  const [reactiveSkips, setReactiveSkips] = useState<Record<string, string[]>>({});
  const [rejectedEventIds, setRejectedEventIds] = useState<Set<string>>(new Set());
  const [resolvedReactives, setResolvedReactives] = useState<Set<string>>(new Set());
  const stopRef = useRef(false);
  const seenBookedRef = useRef<Set<string>>(new Set());
  const resetEpochRef = useRef(0);
  const resetInFlightRef = useRef(false);

  // Polling loop
  useEffect(() => {
    stopRef.current = false;
    let timer: ReturnType<typeof setTimeout>;
    const tick = async () => {
      if (stopRef.current) return;
      try {
        const s = normalizeSnapshot(await api.state());
        if (!resetInFlightRef.current) setSnapshot(s);
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

  const refreshCalendarFixtureStatus = useCallback(async () => {
    try {
      setCalendarFixtureStatus(await api.calendarDemoStatus());
    } catch {
      // ignore — server might be restarting
    }
  }, []);

  useEffect(() => {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const tick = async () => {
      if (stopped) return;
      await refreshCalendarFixtureStatus();
      timer = setTimeout(tick, CALENDAR_FIXTURE_POLL_MS);
    };
    tick();
    return () => {
      stopped = true;
      clearTimeout(timer!);
    };
  }, [refreshCalendarFixtureStatus]);

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
      const epoch = resetEpochRef.current;
      setBusy(true);
      try {
        await fn(...args);
        // bump immediately for snappier UI
        const s = normalizeSnapshot(await api.state());
        if (resetEpochRef.current === epoch) setSnapshot(s);
      } catch {
        // Demo resilience: a timed-out request should not leave controls inert.
      } finally {
        if (resetEpochRef.current === epoch) setBusy(false);
      }
    };
  }, []);

  const send = wrap((userId: string, text: string) => api.sendMessage(userId, text));
  const triggerProactive = wrap(() => api.propose());
  // Custom (not via `wrap`) so we can flip the viewer's approval flag
  // optimistically — the avatar turns on the instant they tap, instead
  // of waiting for the round-trip + state refresh. The poll reconciles
  // any drift within ~1s.
  const approve = useCallback(async (userId: string) => {
    const epoch = resetEpochRef.current;
    setBusy(true);
    setSnapshot((prev) => {
      const p = prev.current_proposal;
      if (!p || !(userId in p.approvals) || p.approvals[userId]) return prev;
      return {
        ...prev,
        current_proposal: {
          ...p,
          approvals: { ...p.approvals, [userId]: true },
        },
      };
    });
    try {
      await api.approve(userId);
      const s = normalizeSnapshot(await api.state());
      if (resetEpochRef.current === epoch) setSnapshot(s);
    } catch {
      // Keep the optimistic approval and let polling reconcile.
    } finally {
      if (resetEpochRef.current === epoch) setBusy(false);
    }
  }, []);
  const dismissProposal = wrap(async () => {
    const evtId = snapshot.current_proposal?.event.id;
    await api.dismissProposal();
    if (evtId) await api.dismissIdea(evtId).catch(() => {});
  });
  const swapAlternate = wrap(() => api.swapAlternate());
  const dismissIdea = wrap((eventId: string) => api.dismissIdea(eventId));
  const hideIdea = wrap((eventId: string, userId: string) =>
    api.hideIdea(eventId, userId)
  );
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
  const clearLocalDemoState = () => {
    seenBookedRef.current = new Set();
    setPlannedEvents([]);
    setCelebrations([]);
    setReactiveSkips({});
    setRejectedEventIds(new Set());
    setResolvedReactives(new Set());
  };

  const reset = () => {
    resetEpochRef.current += 1;
    clearLocalDemoState();
    setSnapshot((prev) => ({
      ...prev,
      messages: [],
      current_proposal: null,
      nest_warmth: 30,
      last_booking: null,
      ideas: [],
      hatch_typing: false,
    }));
    setBusy(false);
    resetInFlightRef.current = true;

    const epoch = resetEpochRef.current;
    api.forceReset();
    window.setTimeout(() => {
      api
        .state()
        .then((raw) => {
          resetInFlightRef.current = false;
          if (resetEpochRef.current === epoch) setSnapshot(normalizeSnapshot(raw));
        })
        .catch(() => {
          resetInFlightRef.current = false;
        });
    }, 350);
  };
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

  const seedCalendarFixtures = async () => {
    setCalendarFixtureBusy(true);
    setCalendarFixtureMessage("seeding…");
    try {
      const r = await api.seedCalendarDemo();
      setCalendarFixtureStatus(r.status);
      setCalendarFixtureMessage(`seeded ${r.created_total}`);
    } catch {
      setCalendarFixtureMessage("seed failed");
    } finally {
      setCalendarFixtureBusy(false);
      setTimeout(() => setCalendarFixtureMessage(null), 3000);
    }
  };

  const deleteCalendarFixtures = async () => {
    setCalendarFixtureBusy(true);
    setCalendarFixtureMessage("clearing…");
    try {
      const r = await api.deleteCalendarDemo();
      setCalendarFixtureStatus(r.status);
      setCalendarFixtureMessage(`cleared ${r.deleted_total}`);
    } catch {
      setCalendarFixtureMessage("clear failed");
    } finally {
      setCalendarFixtureBusy(false);
      setTimeout(() => setCalendarFixtureMessage(null), 3000);
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
    calendarFixtureStatus,
    calendarFixtureBusy,
    calendarFixtureMessage,
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
    hideIdea,
    proposeIdea,
    proposeReactiveOption,
    skipReactiveOption,
    reset,
    setWarmth,
    onWipe,
    seedCalendarFixtures,
    deleteCalendarFixtures,
    demoLakers,
  };
}

export type GroupActions = ReturnType<typeof useGroupState>;
