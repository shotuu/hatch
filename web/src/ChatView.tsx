import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import AgentMessage from "./AgentMessage";
import ChatHeader from "./ChatHeader";
import DemoControls from "./DemoControls";
import HatchLogo from "./HatchLogo";
import MessageBubble from "./MessageBubble";
import ReactiveReply from "./ReactiveReply";
import { propose, react, ProposeResponse } from "./api";
import type { ChatMsg, User } from "./types";

const USERS: User[] = [
  { id: "maya", name: "Maya", color: "#F472B6" },
  { id: "jordan", name: "Jordan", color: "#60A5FA" },
  { id: "priya", name: "Priya", color: "#34D399" },
  { id: "you", name: "You", color: "#FBBF24" },
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

      <div ref={scrollRef} className="flex-1 overflow-y-auto py-2 no-scrollbar">
        <AnimatePresence>
          {proposal && (
            <AgentMessage
              key="proposal"
              proposal={proposal}
              onBooked={(d) => setExpiryDays(d)}
            />
          )}
        </AnimatePresence>

        <AnimatePresence initial={false}>
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
        </AnimatePresence>

        <AnimatePresence>{busy && <TypingDots />}</AnimatePresence>
      </div>

      <div className="px-3 pt-2 pb-2 flex items-center gap-2 border-t border-ink-faint/40 bg-cream-50">
        <button className="w-9 h-9 rounded-full bg-cream-200 flex items-center justify-center text-ink-muted shrink-0">
          +
        </button>
        <div className="flex-1 rounded-full bg-white ring-1 ring-ink-faint/50 px-4 py-2 text-[14px] text-ink-subtle shadow-bubble">
          iMessage
        </div>
        <motion.button
          whileTap={{ scale: 0.92 }}
          className="w-9 h-9 rounded-full bg-coral-500 flex items-center justify-center text-white shadow-warm shrink-0"
        >
          ↑
        </motion.button>
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
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 4 }}
      className="px-3 py-1 flex items-end gap-2"
    >
      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-yolk to-coral-500 flex items-center justify-center shadow-bubble">
        <HatchLogo size={14} />
      </div>
      <div className="rounded-2xl rounded-bl-md bg-white ring-1 ring-ink-faint/40 px-4 py-3 flex gap-1 shadow-bubble">
        <Dot delay="-0.32s" />
        <Dot delay="-0.16s" />
        <Dot delay="0s" />
      </div>
    </motion.div>
  );
}

function Dot({ delay }: { delay: string }) {
  return (
    <span
      className="w-1.5 h-1.5 rounded-full bg-ink-subtle animate-bounce"
      style={{ animationDelay: delay }}
    />
  );
}
