import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import AgentMessage from "./AgentMessage";
import ChatHeader from "./ChatHeader";
import HatchLogo from "./HatchLogo";
import IdeasPanel from "./IdeasPanel";
import MessageBubble from "./MessageBubble";
import MessageInput from "./MessageInput";
import ReactiveReply from "./ReactiveReply";
import type { GroupActions } from "./state";
import type { User } from "./types";

type Props = {
  viewer: User;
  actions: GroupActions;
};

export default function ChatView({ viewer, actions }: Props) {
  const { snapshot, busy, send, approve, dismissProposal, swapAlternate, proposeIdea, dismissIdea } = actions;
  const { messages, current_proposal, expiry_days, users, ideas } = snapshot;
  const scrollRef = useRef<HTMLDivElement>(null);
  const [ideasOpen, setIdeasOpen] = useState(false);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages.length, current_proposal?.id, current_proposal?.status]);

  const usersById = Object.fromEntries(users.map((u) => [u.id, u]));

  return (
    <div className="flex flex-col h-full relative">
      <ChatHeader
        tripName="LA Friends"
        members={users}
        expiryDays={expiry_days}
        onOpenIdeas={() => setIdeasOpen(true)}
        ideasCount={ideas.length}
      />

      <div ref={scrollRef} className="flex-1 overflow-y-auto py-2 no-scrollbar">
        <AnimatePresence>
          {current_proposal && current_proposal.status !== "skipped" && (
            <AgentMessage
              key={current_proposal.id}
              proposal={current_proposal}
              viewer={viewer}
              members={users}
              onApprove={() => approve(viewer.id)}
              onSkip={() => dismissProposal()}
              onSwap={() => swapAlternate()}
            />
          )}
        </AnimatePresence>

        <AnimatePresence initial={false}>
          {messages.map((m) => {
            if (m.kind === "user") {
              const author = (m.author_id && usersById[m.author_id]) || {
                id: m.author_id || "?",
                name: "?",
                color: "#888",
              };
              return (
                <MessageBubble
                  key={m.id}
                  author={author}
                  text={m.text || ""}
                  ts={m.ts}
                  isMe={m.author_id === viewer.id}
                />
              );
            }
            return (
              <ReactiveReply
                key={m.id}
                query={m.query || ""}
                matches={m.matches || []}
                onProposeToGroup={(eid) => proposeIdea(eid)}
              />
            );
          })}
        </AnimatePresence>

        <AnimatePresence>{busy && <TypingDots />}</AnimatePresence>
      </div>

      <MessageInput
        viewerName={viewer.name}
        onSend={(text) => send(viewer.id, text)}
        disabled={busy}
      />

      <IdeasPanel
        open={ideasOpen}
        ideas={ideas}
        onClose={() => setIdeasOpen(false)}
        onPropose={(eid) => {
          proposeIdea(eid);
          setIdeasOpen(false);
        }}
        onDismiss={(eid) => dismissIdea(eid)}
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
