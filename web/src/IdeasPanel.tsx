import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import HatchLogo from "./HatchLogo";
import type { Event, Idea, User } from "./types";

type Props = {
  open: boolean;
  ideas: Idea[];
  plannedEvents: Event[];
  rejectedEventIds: Set<string>;
  viewer: User;
  onClose: () => void;
  onPropose: (eventId: string) => void;
  onDismiss: (eventId: string) => void;
};

const SOURCE_LABEL: Record<Idea["source"], string> = {
  reactive: "from chat",
  proposal: "proposed",
  alternate: "alternate",
};

const SOURCE_STYLE: Record<Idea["source"], string> = {
  reactive: "bg-lavender/15 text-[#6B5BB5] ring-lavender/30",
  proposal: "bg-coral-100 text-coral-700 ring-coral-200",
  alternate: "bg-yolk/20 text-coral-700 ring-yolk/40",
};

const DEMO_LOCALE = "en-US";
const DEMO_TIME_ZONE = "America/Los_Angeles";

export default function IdeasPanel({
  open,
  ideas,
  plannedEvents,
  rejectedEventIds,
  viewer,
  onClose,
  onPropose,
  onDismiss,
}: Props) {
  const plannedEventIds = new Set(plannedEvents.map((e) => e.id));
  const isTerminal = (idea: Idea) =>
    plannedEventIds.has(idea.event.id) || rejectedEventIds.has(idea.event.id);
  // "Hidden for me" means either a global dismiss OR this viewer is in the
  // per-user `hidden` list. The same idea can still be visible (and ranked
  // lower) for other viewers — that's the whole point of the new behavior.
  const personallyHidden = (idea: Idea) =>
    idea.dismissed || (idea.hidden ?? []).includes(viewer.id);
  const activeIdeas = ideas.filter((i) => !personallyHidden(i) && !isTerminal(i));
  const hiddenIdeas = ideas.filter((i) => personallyHidden(i) && !isTerminal(i));
  const [hiddenOpen, setHiddenOpen] = useState(false);

  useEffect(() => {
    if (!open) setHiddenOpen(false);
  }, [open]);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* backdrop within phone */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-ink/30 z-40"
          />
          {/* slide-in panel */}
          <motion.aside
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 360, damping: 38 }}
            className="absolute top-0 right-0 bottom-0 w-[85%] bg-cream-50 z-50 shadow-warmlg flex flex-col"
          >
            <header className="px-4 pt-14 pb-3 border-b border-ink-faint/40 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <HatchLogo size={20} />
                <div>
                  <div className="text-[14px] font-semibold text-ink leading-tight">
                    Ideas in the air
                  </div>
                  <div className="text-[10px] text-ink-subtle">
                    Things y'all've been talking about
                  </div>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-ink-muted text-[18px] leading-none px-2"
                aria-label="Close"
              >
                ×
              </button>
            </header>

            <div className="flex-1 overflow-y-auto no-scrollbar p-3 space-y-2">
              {activeIdeas.length === 0 &&
                hiddenIdeas.length === 0 &&
                plannedEvents.length === 0 && (
                  <div className="text-center py-12 px-6">
                    <div className="text-[13px] text-ink-muted">
                      Nothing yet. Hatch will surface anything y'all bring up here.
                    </div>
                  </div>
                )}

              {plannedEvents.length > 0 && (
                <div className="pb-2">
                  <div className="text-[10px] uppercase tracking-wider font-semibold text-[#1F7A4A] mb-2 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-mint" />
                    Planned · {plannedEvents.length}
                  </div>
                  <div className="space-y-2">
                    {plannedEvents.map((e) => {
                      const when = new Date(e.datetime);
                      return (
                        <motion.div
                          key={e.id}
                          layout
                          initial={{ opacity: 0, y: 6, scale: 0.98 }}
                          animate={{ opacity: 1, y: 0, scale: 1 }}
                          exit={{ opacity: 0, x: 30 }}
                          transition={{ type: "spring", stiffness: 320, damping: 26 }}
                          className="rounded-2xl bg-mint/12 ring-1 ring-mint/40 p-3 shadow-bubble relative overflow-hidden"
                        >
                          <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-mint text-white flex items-center justify-center text-[11px] font-bold">
                            ✓
                          </div>
                          <div className="text-[9px] uppercase tracking-wider font-semibold text-[#1F7A4A] mb-1">
                            Booked
                          </div>
                          <div className="text-[13px] font-semibold text-ink leading-tight pr-6">
                            {e.title}
                          </div>
                          <div className="text-[11px] text-ink-muted mt-1">
                            {e.location} ·{" "}
                            {when.toLocaleDateString(DEMO_LOCALE, {
                              weekday: "short",
                              month: "short",
                              day: "numeric",
                              timeZone: DEMO_TIME_ZONE,
                            })}
                            {" · "}
                            {when.toLocaleTimeString(DEMO_LOCALE, {
                              hour: "numeric",
                              minute: "2-digit",
                              timeZone: DEMO_TIME_ZONE,
                            })}
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              )}

              {activeIdeas.length > 0 && (
                <div className="text-[10px] uppercase tracking-wider font-semibold text-ink-muted mb-1 mt-1 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-coral-500" />
                  Ideas in the air · {activeIdeas.length}
                </div>
              )}

              {activeIdeas.map((idea, i) => (
                <IdeaCard
                  key={idea.event.id}
                  idea={idea}
                  index={i}
                  showHide
                  onPropose={onPropose}
                  onDismiss={onDismiss}
                />
              ))}

              {hiddenIdeas.length > 0 && (
                <div className="pt-3 mt-2 border-t border-ink-faint/40">
                  <motion.button
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setHiddenOpen((v) => !v)}
                    className="w-full flex items-center justify-between text-[11px] uppercase tracking-wider font-semibold text-ink-muted px-1 py-1"
                    aria-expanded={hiddenOpen}
                  >
                    <span className="flex items-center gap-1.5">
                      <motion.span
                        animate={{ rotate: hiddenOpen ? 90 : 0 }}
                        transition={{ type: "spring", stiffness: 320, damping: 24 }}
                        className="inline-block leading-none text-[10px]"
                      >
                        ▸
                      </motion.span>
                      Hidden
                    </span>
                    <span className="text-ink-subtle">{hiddenIdeas.length}</span>
                  </motion.button>

                  <AnimatePresence initial={false}>
                    {hiddenOpen && (
                      <motion.div
                        key="hidden-body"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.22 }}
                        className="overflow-hidden"
                      >
                        <div className="pt-2 space-y-2">
                          {hiddenIdeas.map((idea) => (
                            <IdeaCard
                              key={idea.event.id}
                              idea={idea}
                              index={0}
                              showHide={false}
                              onPropose={onPropose}
                              onDismiss={onDismiss}
                            />
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

type IdeaCardProps = {
  idea: Idea;
  index: number;
  showHide: boolean;
  onPropose: (eventId: string) => void;
  onDismiss: (eventId: string) => void;
};

function IdeaCard({ idea, index, showHide, onPropose, onDismiss }: IdeaCardProps) {
  const e = idea.event;
  const when = new Date(e.datetime);
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: 30 }}
      transition={{ delay: index * 0.04 }}
      className="rounded-2xl bg-white ring-1 ring-ink-faint/40 p-3 shadow-bubble"
    >
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className="text-[13px] font-semibold text-ink leading-tight flex-1">
          {e.title}
        </div>
        <span
          className={`text-[9px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded ring-1 ${SOURCE_STYLE[idea.source]}`}
        >
          {SOURCE_LABEL[idea.source]}
        </span>
      </div>
      <div className="text-[11px] text-ink-muted">
        {e.location} ·{" "}
        {when.toLocaleDateString(DEMO_LOCALE, {
          weekday: "short",
          month: "short",
          day: "numeric",
          timeZone: DEMO_TIME_ZONE,
        })}{" "}
        ·{" "}
        <span className={e.price === 0 ? "text-mint font-semibold" : ""}>
          {e.price === 0 ? "Free" : `$${e.price}`}
        </span>
      </div>
      {idea.score > 0 && (
        <div className="mt-1 text-[10px] text-ink-subtle">
          {"●".repeat(Math.min(idea.score, 5))}
          <span className="text-ink-faint">
            {"●".repeat(Math.max(0, 5 - Math.min(idea.score, 5)))}
          </span>{" "}
          match
        </div>
      )}
      <div className="mt-2 flex gap-1.5">
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={() => onPropose(e.id)}
          className="flex-1 rounded-full bg-coral-500 text-white text-[12px] font-semibold py-1.5 hover:bg-coral-600 transition-colors"
        >
          Propose to group
        </motion.button>
        {showHide && (
          <motion.button
            whileTap={{ scale: 0.97 }}
            onClick={() => onDismiss(e.id)}
            className="rounded-full bg-white ring-1 ring-ink-faint/50 text-[12px] font-medium py-1.5 px-3 text-ink-muted hover:text-ink"
          >
            Hide
          </motion.button>
        )}
      </div>
    </motion.div>
  );
}
