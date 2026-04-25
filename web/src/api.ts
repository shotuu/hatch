import type { Event, Proposal } from "./types";

export type ProposeResponse = Proposal | { ok: false; reason: string };

export type BookResponse = {
  ok: boolean;
  event_id?: string;
  calendars_written?: number;
  expiry_reset_days?: number;
  reason?: string;
};

export type ReactResponse = { matches: Event[] };

const BASE = "/api";

export async function propose(): Promise<ProposeResponse> {
  const r = await fetch(`${BASE}/propose`, { method: "POST" });
  return r.json();
}

export async function book(eventId: string): Promise<BookResponse> {
  const r = await fetch(`${BASE}/book`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ event_id: eventId }),
  });
  return r.json();
}

export async function react(query: string): Promise<ReactResponse> {
  const r = await fetch(`${BASE}/react`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  return r.json();
}
