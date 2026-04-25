import { AnimatePresence, motion } from "framer-motion";
import AgentMessage from "./AgentMessage";
import ChatHeader from "./ChatHeader";
import HatchLogo from "./HatchLogo";
import MessageBubble from "./MessageBubble";
import ReactiveReply from "./ReactiveReply";
import { ME_ID, USERS, type HatchState } from "./state";

type Props = Pick<
  HatchState,
  "expiryDays" | "messages" | "proposal" | "busy" | "scrollRef" | "onBooked"
>;

export default function ChatView({
  expiryDays,
  messages,
  proposal,
  busy,
  scrollRef,
  onBooked,
}: Props) {
  return (
    <div className="flex flex-col h-full">
      <ChatHeader tripName="LA Friends" members={USERS} expiryDays={expiryDays} />

      <div ref={scrollRef} className="flex-1 overflow-y-auto py-2 no-scrollbar">
        <AnimatePresence>
          {proposal && (
            <AgentMessage key="proposal" proposal={proposal} onBooked={onBooked} />
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
                isMe={m.author.id === ME_ID}
              />
            ) : (
              <ReactiveReply key={m.id} query={m.query} matches={m.matches} />
            )
          )}
        </AnimatePresence>

        <AnimatePresence>{busy && <TypingDots />}</AnimatePresence>
      </div>

      <div className="px-3 pt-2 pb-3 flex items-center gap-2 border-t border-ink-faint/40 bg-cream-50">
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
