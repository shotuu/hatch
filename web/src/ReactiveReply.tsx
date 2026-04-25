import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import HatchLogo from "./HatchLogo";
import type { Event } from "./types";

type Props = {
  query: string;
  matches: Event[];
  onProposeToGroup: (eventId: string) => void;
};

export default function ReactiveReply({ query, matches, onProposeToGroup }: Props) {
  const [open, setOpen] = useState(false);

  if (matches.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 360, damping: 28 }}
      className="px-3 py-1 flex items-end gap-2"
    >
      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-yolk to-coral-500 flex items-center justify-center shrink-0 shadow-bubble">
        <HatchLogo size={14} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="text-[10px] text-coral-700 mb-0.5 ml-2 font-medium">
          Hatch · just now
        </div>

        <motion.div
          layout
          className="w-full text-left rounded-2xl rounded-bl-md bg-white ring-1 ring-coral-100 px-3.5 py-2.5 text-[14px] text-ink shadow-bubble"
        >
          <button
            onClick={() => setOpen(!open)}
            className="w-full flex items-center justify-between gap-2 text-left"
          >
            <span>
              Found <b className="text-coral-600">{matches.length}</b> option
              {matches.length === 1 ? "" : "s"} for{" "}
              <span className="text-ink-muted">"{query}"</span>
            </span>
            <motion.span
              animate={{ rotate: open ? 180 : 0 }}
              transition={{ duration: 0.25 }}
              className="text-[11px] text-ink-subtle"
            >
              ▾
            </motion.span>
          </button>

          <AnimatePresence initial={false}>
            {open && (
              <motion.div
                key="content"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
                className="overflow-hidden"
              >
                <div className="mt-2.5 space-y-2">
                  {matches.slice(0, 3).map((e, i) => (
                    <motion.div
                      key={e.id}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.06 }}
                      className="rounded-xl bg-cream-100 ring-1 ring-ink-faint/40 p-2.5"
                    >
                      <div className="text-[13px] font-semibold text-ink leading-tight">
                        {e.title}
                      </div>
                      <div className="text-[11px] text-ink-muted mt-1">
                        {e.location} ·{" "}
                        {new Date(e.datetime).toLocaleDateString(undefined, {
                          weekday: "short",
                          month: "short",
                          day: "numeric",
                        })}{" "}
                        ·{" "}
                        <span className={e.price === 0 ? "text-mint font-semibold" : "text-ink-muted"}>
                          {e.price === 0 ? "Free" : `$${e.price}`}
                        </span>
                      </div>
                      <div className="mt-2">
                        <motion.button
                          whileTap={{ scale: 0.97 }}
                          onClick={() => onProposeToGroup(e.id)}
                          className="rounded-full bg-coral-500 text-white text-[11px] font-semibold px-2.5 py-1 hover:bg-coral-600 transition-colors"
                        >
                          Propose to group
                        </motion.button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </motion.div>
  );
}
