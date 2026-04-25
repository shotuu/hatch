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
  onBack?: () => void;
};

export default function ChatView({ viewer, actions, onBack }: Props) {
  const {
    snapshot,
    busy,
    plannedEvents,
    reactiveSkips,
    rejectedEventIds,
    send,
    approve,
    dismissProposal,
    skipProposal,
    swapAlternate,
    proposeIdea,
    proposeReactiveOption,
    skipReactiveOption,
    dismissIdea,
  } = actions;
  const { messages, current_proposal, nest_warmth, nest_max, users, ideas } = snapshot;
  const proposalActive =
    !!current_proposal && current_proposal.status !== "skipped";
  const proposedEventId = current_proposal?.event.id ?? null;
  const bookedEventIds = new Set(plannedEvents.map((e) => e.id));
  const terminalIdeaIds = new Set([...bookedEventIds, ...rejectedEventIds]);
  const visibleIdeasCount = ideas.filter(
    (i) => !i.dismissed && !terminalIdeaIds.has(i.event.id),
  ).length;

  const scrollRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const [ideasOpen, setIdeasOpen] = useState(false);
  const [proposalCollapsed, setProposalCollapsed] = useState(false);
  const [conversationStart] = useState(() => formatPTNow());

  useEffect(() => {
    const scroller = scrollRef.current;
    const content = contentRef.current;
    if (!scroller || !content) return;
    scroller.scrollTop = scroller.scrollHeight;
    let prevHeight = content.offsetHeight;
    const ro = new ResizeObserver(() => {
      const next = content.offsetHeight;
      if (next > prevHeight) {
        scroller.scrollTop = scroller.scrollHeight;
      }
      prevHeight = next;
    });
    ro.observe(content);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    if (current_proposal?.id) setProposalCollapsed(false);
  }, [current_proposal?.id]);

  const usersById = Object.fromEntries(users.map((u) => [u.id, u]));

  return (
    <div className="flex flex-col h-full relative">
      <ChatHeader
        tripName="LA Friends"
        members={users}
        nestWarmth={nest_warmth}
        nestMax={nest_max}
        onOpenIdeas={() => setIdeasOpen(true)}
        ideasCount={visibleIdeasCount}
        plannedCount={plannedEvents.length}
        onBack={onBack}
      />

      <div className="flex-1 relative">
        <div className="absolute inset-x-0 top-0 z-20 pointer-events-none">
          <AnimatePresence>
            {proposalActive && current_proposal && (
              <div className="pointer-events-auto bg-cream-50 border-b border-ink-faint/30 shadow-warm pb-1">
                <AgentMessage
                  key={current_proposal.id}
                  proposal={current_proposal}
                  viewer={viewer}
                  members={users}
                  collapsed={proposalCollapsed}
                  onToggleCollapse={() => setProposalCollapsed((v) => !v)}
                  onApprove={() => approve(viewer.id)}
                  onSkip={() => skipProposal(viewer.id)}
                  onSwap={() => swapAlternate()}
                />
              </div>
            )}
          </AnimatePresence>
        </div>

        <div
          ref={scrollRef}
          className="absolute inset-0 overflow-y-auto py-2 no-scrollbar scroll-smooth [overflow-anchor:none]"
        >
          <div ref={contentRef}>
            <div className="text-center text-[11px] text-ink-subtle font-medium py-2">
              {conversationStart}
            </div>
            <AnimatePresence initial={false}>
              {messages.map((m) => {
                if (m.kind === "celebration") {
                  return (
                    <motion.div
                      key={m.id}
                      initial={{ opacity: 0, y: 8, scale: 0.96 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      transition={{ type: "spring", stiffness: 320, damping: 26 }}
                      className="px-3 py-2 flex justify-center"
                    >
                      <div className="rounded-2xl bg-gradient-to-br from-mint/25 via-cream-50 to-yolk/15 ring-1 ring-mint/40 px-3.5 py-2 text-center shadow-bubble max-w-[80%]">
                        <div className="text-[12.5px] font-semibold text-[#1F7A4A]">
                          {m.text}
                        </div>
                        <div className="text-[11px] text-ink-muted mt-0.5">
                          {m.event_title} · on every calendar
                        </div>
                      </div>
                    </motion.div>
                  );
                }
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
                if (m.kind === "proposal") {
                  return null;
                }
                return (
                  <ReactiveReply
                    key={m.id}
                    query={m.query || ""}
                    matches={m.matches || []}
                    viewer={viewer}
                    members={users}
                    skipsByEvent={reactiveSkips}
                    bookedEventIds={bookedEventIds}
                    proposedEventId={proposedEventId}
                    onProposeToGroup={(eid) =>
                      proposeReactiveOption(eid, m.id, viewer.id)
                    }
                    onSkip={(eid) => skipReactiveOption(eid, viewer.id)}
                  />
                );
              })}
            </AnimatePresence>
          </div>
        </div>

        <AnimatePresence>
          {busy && (
            <div className="absolute bottom-1 left-0 right-0 z-10 pointer-events-none">
              <TypingDots />
            </div>
          )}
        </AnimatePresence>
      </div>

      <MessageInput
        viewerName={viewer.name}
        onSend={(text) => send(viewer.id, text)}
        disabled={busy}
      />

      <IdeasPanel
        open={ideasOpen}
        ideas={ideas}
        plannedEvents={plannedEvents}
        rejectedEventIds={rejectedEventIds}
        onClose={() => setIdeasOpen(false)}
        onPropose={(eid) => {
          proposeIdea(eid, viewer.id);
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

function formatPTNow() {
  const now = new Date();
  const date = now.toLocaleDateString("en-US", {
    timeZone: "America/Los_Angeles",
    weekday: "short",
    month: "short",
    day: "numeric",
  });
  const time = now.toLocaleTimeString("en-US", {
    timeZone: "America/Los_Angeles",
    hour: "numeric",
    minute: "2-digit",
  });
  return `${date} · ${time}`;
}
