export type User = {
  id: string;
  name: string;
  color: string;
};

export type Event = {
  id: string;
  title: string;
  datetime: string;
  duration_minutes: number;
  location: string;
  price: number;
  url: string;
  tags: string[];
  _score?: number;
};

export type ServerMsg = {
  id: string;
  kind: "user" | "reactive" | "proposal" | "celebration";
  ts: string;
  author_id?: string | null;
  text?: string | null;
  parent_id?: string | null;
  query?: string | null;
  matches?: Event[];
  proposal_id?: string | null;
  event_title?: string | null;
};

export type Proposal = {
  id: string;
  window: { start: string; end: string };
  event: Event;
  alternates: Event[];
  approvals: Record<string, boolean>;
  status: "pending" | "booking" | "booked" | "skipped";
  created_at: string;
  booking?: {
    ok: boolean;
    calendars_written?: number;
    nest_restore?: number;
    failures?: string[];
  } | null;
};

export type Idea = {
  event: Event;
  source: "reactive" | "proposal" | "alternate";
  score: number;
  seen_at: string;
  dismissed: boolean;
};

export type GroupSnapshot = {
  messages: ServerMsg[];
  current_proposal: Proposal | null;
  expiry_days?: number;
  nest_warmth: number;
  nest_max: number;
  last_booking: any;
  ideas: Idea[];
  users: User[];
};
