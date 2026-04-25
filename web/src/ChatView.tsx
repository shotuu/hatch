import { useEffect, useRef, useState } from "react";
import AgentMessage from "./AgentMessage";
import ChatHeader from "./ChatHeader";
import DemoControls from "./DemoControls";
import MessageBubble from "./MessageBubble";
import ReactiveReply from "./ReactiveReply";
import { propose, react, ProposeResponse } from "./api";
import type { ChatMsg, User } from "./types";

const USERS: User[] = [
  { id: "maya", name: "Maya", color: "#f472b6" },
  { id: "jordan", name: "Jordan", color: "#60a5fa" },
  { id: "priya", name: "Priya", color: "#34d399" },
  { id: "you", name: "You", color: "#fbbf24" },
];

const SEED_MESSAGES: ChatMsg[] = [
  {
    kind: "user",
    id: "m1",
    author: USERS[0],
    text: "miss y'all 😭",
    ts: "3 weeks ago",
  },
  {
    kind: "user",
    id: "m2",
    author: USERS[1],
    text: "we gotta do something soon fr",
    ts: "3 weeks ago",
  },
  {
    kind: "user",
    id: "m3",
    author: USERS[2],
    text: "down whenever",
    ts: "3 weeks ago",
  },
  {
    kind: "user",
    id: "m4",
    author: USERS[3],
    text: "lmk",
    ts: "2 weeks ago",
  },
];

export default function ChatView() {
  const [expiryDays, setExpiryDays] = useState(6);
  const [messages, setMessages] = useState<ChatMsg[]>(SEED_MESSAGES);
  const [proposal, setProposal] = useState<
    Extract<ProposeResponse, { ok: true }> | null
  >(null);
  const [busy, setBusy] = useState(false);
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
      author: USERS[0],
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

  return (
    <div className="flex flex-col h-full">
      <ChatHeader tripName="LA Friends" members={USERS} expiryDays={expiryDays} />

      <div ref={scrollRef} className="flex-1 overflow-y-auto py-2">
        {proposal && (
          <AgentMessage
            proposal={proposal}
            onBooked={(d) => setExpiryDays(d)}
          />
        )}

        {messages.map((m) =>
          m.kind === "user" ? (
            <MessageBubble
              key={m.id}
              author={m.author}
              text={m.text}
              ts={m.ts}
              isMe={m.author.id === "you"}
            />
          ) : (
            <ReactiveReply key={m.id} query={m.query} matches={m.matches} />
          )
        )}

        {busy && <TypingDots />}
      </div>

      <div className="px-3 pt-2 pb-1.5 flex items-center gap-2">
        <div className="flex-1 rounded-full bg-neutral-800 px-3 py-2 text-[13px] text-neutral-500">
          iMessage
        </div>
        <button className="w-9 h-9 rounded-full bg-blue-500 flex items-center justify-center text-white text-lg">
          ↑
        </button>
      </div>

      <DemoControls
        onReactiveDemo={triggerReactive}
        onProactiveDemo={triggerProactive}
        onReset={reset}
        busy={busy}
      />
    </div>
  );
}

function TypingDots() {
  return (
    <div className="px-3 py-1 flex items-end gap-2">
      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-400 to-fuchsia-400 flex items-center justify-center text-[11px]">
        ✨
      </div>
      <div className="rounded-2xl rounded-bl-md bg-neutral-800 px-4 py-3 flex gap-1">
        <span className="w-1.5 h-1.5 rounded-full bg-neutral-500 animate-bounce [animation-delay:-0.3s]" />
        <span className="w-1.5 h-1.5 rounded-full bg-neutral-500 animate-bounce [animation-delay:-0.15s]" />
        <span className="w-1.5 h-1.5 rounded-full bg-neutral-500 animate-bounce" />
      </div>
    </div>
  );
}
