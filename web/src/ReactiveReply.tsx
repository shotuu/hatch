import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import HatchLogo from "./HatchLogo";
import type { Event, User } from "./types";

type Props = {
  query: string;
  matches: Event[];
  onProposeToGroup: (eventId: string) => void;
  viewer?: User;
  members?: User[];
  skipsByEvent?: Record<string, string[]>;
  bookedEventIds?: Set<string>;
  proposedEventId?: string | null;
  onSkip?: (eventId: string) => void;
};

export default function ReactiveReply({
  query,
  matches,
  onProposeToGroup,
  viewer,
  members = [],
  skipsByEvent = {},
  bookedEventIds = new Set(),
  proposedEventId = null,
  onSkip,
}: Props) {
  const [open, setOpen] = useState(true);

  const visibleMatches = matches.filter((e) => !bookedEventIds.has(e.id));

  if (visibleMatches.length === 0) return null;

  const usersById = Object.fromEntries(members.map((m) => [m.id, m]));

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
              Found <b className="text-coral-600">{visibleMatches.length}</b> option
              {visibleMatches.length === 1 ? "" : "s"} for{" "}
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
                  {visibleMatches.slice(0, 3).map((e, i) => (
                    <motion.div
                      key={e.id}
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.06 }}
                    >
                      <OptionCard
                        event={e}
                        proposed={proposedEventId === e.id}
                        skippedBy={(skipsByEvent[e.id] || [])
                          .map((id) => usersById[id])
                          .filter(Boolean) as User[]}
                        viewerSkipped={
                          !!viewer &&
                          (skipsByEvent[e.id] || []).includes(viewer.id)
                        }
                        onPropose={() => onProposeToGroup(e.id)}
                        onSkip={onSkip ? () => onSkip(e.id) : undefined}
                      />
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

type OptionProps = {
  event: Event;
  proposed: boolean;
  skippedBy: User[];
  viewerSkipped: boolean;
  onPropose: () => void;
  onSkip?: () => void;
};

function OptionCard({
  event,
  proposed,
  skippedBy,
  viewerSkipped,
  onPropose,
  onSkip,
}: OptionProps) {
  const unavailable = skippedBy.length > 0;

  return (
    <div
      className={`rounded-xl ring-1 p-2.5 transition-colors ${
        proposed
          ? "bg-mint/12 ring-mint/40"
          : "bg-cream-100 ring-ink-faint/40"
      }`}
    >
      <div className="text-[13px] font-semibold text-ink leading-tight">
        {event.title}
      </div>
      <div className="text-[11px] text-ink-muted mt-1">
        {event.location} ·{" "}
        {new Date(event.datetime).toLocaleDateString(undefined, {
          weekday: "short",
          month: "short",
          day: "numeric",
        })}{" "}
        ·{" "}
        <span
          className={
            event.price === 0 ? "text-mint font-semibold" : "text-ink-muted"
          }
        >
          {event.price === 0 ? "Free" : `$${event.price}`}
        </span>
      </div>
      <div className="mt-2 flex items-center gap-2 flex-wrap">
        {proposed ? (
          <div className="rounded-full bg-mint text-white text-[11px] font-bold px-2.5 py-1 inline-flex items-center gap-1">
            <span aria-hidden>✓</span>
            <span>Proposed</span>
          </div>
        ) : unavailable ? (
          <div className="rounded-full bg-cream-50 ring-1 ring-ink-faint/50 text-ink-muted text-[11px] font-semibold px-2.5 py-1 inline-flex items-center gap-1">
            <span aria-hidden>×</span>
            <span>Not this one</span>
          </div>
        ) : (
          <>
            <motion.button
              whileTap={{ scale: 0.97 }}
              onClick={onPropose}
              className="rounded-full bg-coral-500 text-white text-[11px] font-semibold px-2.5 py-1 hover:bg-coral-600 transition-colors"
            >
              Propose to group
            </motion.button>
            {onSkip && (
              <motion.button
                whileTap={{ scale: 0.97 }}
                onClick={onSkip}
                disabled={viewerSkipped}
                className="rounded-full bg-white ring-1 ring-ink-faint/50 text-ink-muted text-[11px] font-medium px-2.5 py-1 hover:text-ink disabled:opacity-50"
              >
                {viewerSkipped ? "Skipped" : "Skip"}
              </motion.button>
            )}
          </>
        )}
      </div>
      {!proposed && skippedBy.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {skippedBy.map((u) => (
            <span
              key={u.id}
              className="inline-flex items-center gap-1 rounded-full bg-cream-50 ring-1 ring-ink-faint/40 px-1.5 py-0.5 text-[10px] text-ink-muted"
            >
              <span
                className="w-3 h-3 rounded-full text-[8px] font-semibold text-white flex items-center justify-center"
                style={{ background: u.color }}
              >
                {u.name[0]}
              </span>
              {u.name} can't make it
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
