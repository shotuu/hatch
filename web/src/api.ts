import type { GroupSnapshot } from "./types";

const BASE = "/api";
const DEFAULT_TIMEOUT_MS = 12000;

async function fetchJson(path: string, init?: RequestInit, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController();
  const id = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const r = await fetch(`${BASE}${path}`, { ...init, signal: controller.signal });
    return r.json();
  } finally {
    window.clearTimeout(id);
  }
}

async function jpost(path: string, body?: unknown) {
  return fetchJson(path, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
}

export const api = {
  state: async (): Promise<GroupSnapshot> => fetchJson("/state", undefined, 5000),

  sendMessage: (user_id: string, text: string) =>
    jpost("/send_message", { user_id, text }),

  propose: () => jpost("/propose"),
  approve: (user_id: string) => jpost("/approve", { user_id }),
  dismissProposal: () => jpost("/dismiss_proposal"),
  swapAlternate: () => jpost("/swap_alternate"),

  dismissIdea: (event_id: string) => jpost("/dismiss_idea", { event_id }),
  hideIdea: (event_id: string, user_id: string) =>
    jpost("/hide_idea", { event_id, user_id }),
  proposeIdea: (event_id: string, user_id?: string) =>
    jpost("/propose_idea", { event_id, user_id }),

  reset: () => jpost("/reset"),
  forceReset: () => {
    const url = `${BASE}/reset`;
    if (navigator.sendBeacon) {
      const body = new Blob([], { type: "application/json" });
      if (navigator.sendBeacon(url, body)) return;
    }
    fetch(url, { method: "POST", keepalive: true }).catch(() => {});
  },
  wipe: () => jpost("/cleanup"),
  calendarDemoStatus: async () => fetchJson("/calendar_demo/status", undefined, 5000),
  seedCalendarDemo: () => jpost("/calendar_demo/seed"),
  deleteCalendarDemo: () => jpost("/calendar_demo/delete"),

  setWarmth: (days: number, auto_propose = true) =>
    jpost("/set_warmth", { days, auto_propose }),
};
