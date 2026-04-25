import { AnimatePresence, motion } from "framer-motion";
import HatchLogo from "./HatchLogo";
import type { Idea } from "./types";

type Props = {
  open: boolean;
  ideas: Idea[];
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

export default function IdeasPanel({
  open,
  ideas,
  onClose,
  onPropose,
  onDismiss,
}: Props) {
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
              {ideas.length === 0 && (
                <div className="text-center py-12 px-6">
                  <div className="text-[13px] text-ink-muted">
                    Nothing yet. Hatch will surface anything y'all bring up here.
                  </div>
                </div>
              )}

              {ideas.map((idea, i) => {
                const e = idea.event;
                const when = new Date(e.datetime);
                return (
                  <motion.div
                    key={e.id}
                    layout
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, x: 30 }}
                    transition={{ delay: i * 0.04 }}
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
                      {when.toLocaleDateString(undefined, {
                        weekday: "short",
                        month: "short",
                        day: "numeric",
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
                      <motion.button
                        whileTap={{ scale: 0.97 }}
                        onClick={() => onDismiss(e.id)}
                        className="rounded-full bg-white ring-1 ring-ink-faint/50 text-[12px] font-medium py-1.5 px-3 text-ink-muted hover:text-ink"
                      >
                        Hide
                      </motion.button>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
