import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import BookingChecklist from "./BookingChecklist";
import HatchLogo from "./HatchLogo";
import { book, ProposeResponse } from "./api";

type Props = {
  proposal: Extract<ProposeResponse, { ok: true }>;
  onBooked: (days: number) => void;
};

function formatWindow(startISO: string, endISO: string) {
  const s = new Date(startISO);
  const e = new Date(endISO);
  const day = s.toLocaleDateString(undefined, { weekday: "long" });
  const fmt = (d: Date) =>
    d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  return `${day} ${fmt(s)}–${fmt(e)}`;
}

export default function AgentMessage({ proposal, onBooked }: Props) {
  const [state, setState] = useState<"idle" | "booking" | "booked">("idle");
  const windowText = formatWindow(proposal.window.start, proposal.window.end);
  const userNames = proposal.users.map((u) => u.name);

  const onBook = async () => {
    setState("booking");
    await book(proposal.event.id);
  };

  const onChecklistDone = () => {
    setState("booked");
    onBooked(30);
  };

  const eventTime = new Date(proposal.event.datetime).toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  });

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -10, scale: 0.94 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        type: "spring",
        stiffness: 320,
        damping: 26,
        mass: 0.9,
      }}
      className="mx-3 my-3 rounded-[22px] bg-gradient-to-br from-coral-50 via-cream-50 to-yolk/20 ring-1 ring-coral-200/70 p-3.5 shadow-warm relative overflow-hidden"
    >
      {/* soft top sheen */}
      <div className="absolute inset-x-0 top-0 h-12 bg-gradient-to-b from-white/60 to-transparent pointer-events-none" />

      <div className="flex items-center gap-1.5 mb-2 relative">
        <HatchLogo size={16} />
        <div className="text-[11px] uppercase tracking-wider text-coral-700 font-semibold">
          Hatch · pinned
        </div>
      </div>

      <div className="text-[14.5px] leading-snug text-ink relative">
        Y'all are free <b className="text-ink">{windowText}</b>. I found
        something good.
        <motion.div
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.18, duration: 0.4 }}
          className="mt-2.5 rounded-2xl bg-white ring-1 ring-coral-100 p-3 shadow-bubble"
        >
          <div className="text-[14px] font-semibold text-ink leading-tight">
            {proposal.event.title}
          </div>
          <div className="text-[11.5px] text-ink-muted mt-1 flex items-center gap-1.5">
            <span>{proposal.event.location}</span>
            <span className="text-ink-faint">·</span>
            <span>{eventTime}</span>
            <span className="text-ink-faint">·</span>
            <span
              className={
                proposal.event.price === 0 ? "text-mint font-semibold" : ""
              }
            >
              {proposal.event.price === 0 ? "Free" : `$${proposal.event.price}`}
            </span>
          </div>
        </motion.div>
        <div className="mt-2.5 text-ink">Want me to set it up?</div>
      </div>

      <AnimatePresence mode="wait">
        {state === "idle" && (
          <motion.div
            key="idle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="mt-3 grid grid-cols-3 gap-2 relative"
          >
            <motion.button
              whileTap={{ scale: 0.97 }}
              onClick={onBook}
              className="col-span-2 rounded-full bg-coral-500 text-white text-[13.5px] font-semibold py-2.5 shadow-warm hover:bg-coral-600 transition-colors"
            >
              Book it
            </motion.button>
            <motion.button
              whileTap={{ scale: 0.97 }}
              className="rounded-full bg-white ring-1 ring-ink-faint/50 text-[13.5px] py-2.5 text-ink-muted font-medium"
            >
              Skip
            </motion.button>
          </motion.div>
        )}

        {state === "booking" && (
          <motion.div
            key="booking"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <BookingChecklist userNames={userNames} onDone={onChecklistDone} />
          </motion.div>
        )}

        {state === "booked" && (
          <motion.div
            key="booked"
            initial={{ opacity: 0, y: 6, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ type: "spring", stiffness: 400, damping: 24 }}
            className="mt-3 rounded-2xl bg-mint/15 ring-1 ring-mint/40 px-3 py-2.5 text-[13px] text-[#1F7A4A] flex items-center gap-2"
          >
            <span className="w-5 h-5 rounded-full bg-mint text-white flex items-center justify-center text-[11px] font-bold">
              ✓
            </span>
            <span>
              Done. <b>30 more days together</b> — chat is alive again.
            </span>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
