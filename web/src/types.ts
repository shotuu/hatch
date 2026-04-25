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
};

export type Proposal = {
  ok: true;
  window: { start: string; end: string };
  event: Event;
  alternates: Event[];
  users: { id: string; name: string }[];
};

export type ChatMsg =
  | {
      kind: "user";
      id: string;
      author: User;
      text: string;
      ts: string;
    }
  | {
      kind: "reactive";
      id: string;
      parentId: string;
      query: string;
      matches: Event[];
    };
