import { useEffect, useRef, useState } from "react";
import { propose, react, wipe, ProposeResponse } from "./api";
import type { ChatMsg, User } from "./types";

// Keep in sync with data/users.json. TODO: fetch from /api/users instead.
// `daniel` is the demo viewer — bubbles render right-side (isMe).
export const USERS: User[] = [
  { id: "daniel", name: "Daniel", color: "#F472B6" },
  { id: "jono", name: "Jono", color: "#60A5FA" },
  { id: "andrew", name: "Andrew", color: "#34D399" },
];

export const ME_ID = "daniel";

export const SEED_MESSAGES: ChatMsg[] = [
  {
    kind: "user",
    id: "m1",
    author: USERS[1],
    text: "miss y'all 😭",
    ts: "3 weeks ago",
  },
  {
    kind: "user",
    id: "m2",
    author: USERS[2],
    text: "we gotta do something soon fr",
    ts: "3 weeks ago",
  },
  {
    kind: "user",
    id: "m3",
    author: USERS[1],
    text: "down whenever, lmk",
    ts: "2 weeks ago",
  },
];

export type HatchState = ReturnType<typeof useHatchState>;

export function useHatchState() {
  const [expiryDays, setExpiryDays] = useState(6);
  const [messages, setMessages] = useState<ChatMsg[]>(SEED_MESSAGES);
  const [proposal, setProposal] = useState<
    Extract<ProposeResponse, { ok: true }> | null
  >(null);
  const [busy, setBusy] = useState(false);
  const [wipeStatus, setWipeStatus] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, proposal]);

  const triggerProactive = async () => {
    setBusy(true);
    const r = await propose();
    if ("ok" in r && r.ok) setProposal(r);
    setBusy(false);
  };

  const triggerReactive = async () => {
    setBusy(true);
    const userMsg: ChatMsg = {
      kind: "user",
      id: `u${Date.now()}`,
      author: USERS[1], // Jono
      text: "anyone down for the Lakers game next week?",
      ts: "now",
    };
    setMessages((m) => [...m, userMsg]);

    try {
      const r = await react("lakers");
      const reactiveMsg: ChatMsg = {
        kind: "reactive",
        id: `r${Date.now()}`,
        parentId: userMsg.id,
        query: "Lakers game",
        matches: r.matches,
      };
      setTimeout(() => {
        setMessages((m) => [...m, reactiveMsg]);
        setBusy(false);
      }, 700);
    } catch {
      setBusy(false);
    }
  };

  const reset = () => {
    setMessages(SEED_MESSAGES);
    setProposal(null);
    setExpiryDays(6);
  };

  const onWipe = async () => {
    setBusy(true);
    setWipeStatus("wiping…");
    try {
      const r = await wipe();
      setWipeStatus(`wiped ${r.total_deleted} event${r.total_deleted === 1 ? "" : "s"}`);
    } catch {
      setWipeStatus("failed");
    } finally {
      setBusy(false);
      setTimeout(() => setWipeStatus(null), 3000);
    }
  };

  const onBooked = (d: number) => setExpiryDays(d);

  return {
    // data
    expiryDays,
    messages,
    proposal,
    busy,
    wipeStatus,
    scrollRef,
    // handlers
    triggerProactive,
    triggerReactive,
    reset,
    onWipe,
    onBooked,
  };
}
