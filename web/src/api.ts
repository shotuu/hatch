import type { GroupSnapshot } from "./types";

const BASE = "/api";

async function jpost(path: string, body?: unknown) {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  return r.json();
}

export const api = {
  state: async (): Promise<GroupSnapshot> => (await fetch(`${BASE}/state`)).json(),

  sendMessage: (user_id: string, text: string) =>
    jpost("/send_message", { user_id, text }),

  propose: () => jpost("/propose"),
  approve: (user_id: string) => jpost("/approve", { user_id }),
  dismissProposal: () => jpost("/dismiss_proposal"),
  swapAlternate: () => jpost("/swap_alternate"),

  dismissIdea: (event_id: string) => jpost("/dismiss_idea", { event_id }),
  proposeIdea: (event_id: string) => jpost("/propose_idea", { event_id }),

  reset: () => jpost("/reset"),
  wipe: () => jpost("/cleanup"),

  setWarmth: (days: number, auto_propose = true) =>
    jpost("/set_warmth", { days, auto_propose }),
};
