export type ProposeResponse =
  | {
      ok: true;
      window: { start: string; end: string };
      event: {
        id: string;
        title: string;
        datetime: string;
        location: string;
        price: number;
        tags: string[];
      };
      alternates: ProposeResponse extends { ok: true } ? any[] : never;
      users: { id: string; name: string }[];
    }
  | { ok: false; reason: string };

export type BookResponse = {
  ok: boolean;
  event_id?: string;
  calendars_written?: number;
  expiry_reset_days?: number;
  reason?: string;
};

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
