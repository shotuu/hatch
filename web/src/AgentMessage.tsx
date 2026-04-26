import { AnimatePresence, motion } from "framer-motion";
import BookingChecklist from "./BookingChecklist";
import HatchLogo from "./HatchLogo";
import type { Proposal, User } from "./types";

const DEMO_LOCALE = "en-US";
const DEMO_TIME_ZONE = "America/Los_Angeles";

type Props = {
  proposal: Proposal;
  viewer: User;
  members: User[];
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  onApprove: () => void;
  onSkip: () => void;
  onSwap: () => void;
};

function formatWindow(startISO: string, endISO: string) {
  const s = new Date(startISO);
  const e = new Date(endISO);
  const day = s.toLocaleDateString(DEMO_LOCALE, {
    weekday: "long",
    timeZone: DEMO_TIME_ZONE,
  });
  const fmt = (d: Date) =>
    d.toLocaleTimeString(DEMO_LOCALE, {
      hour: "numeric",
      minute: "2-digit",
      timeZone: DEMO_TIME_ZONE,
    });
  return `${day} ${fmt(s)}–${fmt(e)}`;
}

export default function AgentMessage({
  proposal,
  viewer,
  members,
  collapsed = false,
  onToggleCollapse,
  onApprove,
  onSkip,
  onSwap,
}: Props) {
  const windowText = formatWindow(proposal.window.start, proposal.window.end);
  const eventTime = new Date(proposal.event.datetime).toLocaleTimeString(DEMO_LOCALE, {
    hour: "numeric",
    minute: "2-digit",
    timeZone: DEMO_TIME_ZONE,
  });

  const viewerApproved = !!proposal.approvals[viewer.id];
  const approvedCount = Object.values(proposal.approvals).filter(Boolean).length;
  const totalCount = Object.values(proposal.approvals).length;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -10, scale: 0.94 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ type: "spring", stiffness: 320, damping: 26, mass: 0.9 }}
      className="mx-3 my-3 rounded-[22px] bg-gradient-to-br from-coral-50 via-cream-50 to-[#FFF1BF] ring-1 ring-coral-200/70 p-3.5 shadow-warm relative overflow-hidden"
    >
      <div className="absolute inset-x-0 top-0 h-12 bg-gradient-to-b from-white/60 to-transparent pointer-events-none" />

      <div className="flex items-center gap-1.5 relative">
        <HatchLogo size={16} />
        <div className="text-[11px] uppercase tracking-wider text-coral-700 font-semibold">
          Hatch · plan
        </div>
        {collapsed && proposal.status === "pending" && (
          <span className="ml-1.5 text-[10px] text-ink-muted font-medium">
            {approvedCount}/{totalCount} in
          </span>
        )}
        {collapsed && proposal.status === "booking" && (
          <span className="ml-1.5 text-[10px] text-coral-700 font-medium">
            booking…
          </span>
        )}
        {collapsed && proposal.status === "booked" && (
          <span className="ml-1.5 text-[10px] text-[#1F7A4A] font-semibold">
            ✓ booked
          </span>
        )}
        {onToggleCollapse && (
          <motion.button
            whileTap={{ scale: 0.92 }}
            onClick={onToggleCollapse}
            aria-label={collapsed ? "Expand plan" : "Collapse plan"}
            className="ml-auto w-6 h-6 rounded-full bg-white/70 ring-1 ring-coral-200/70 flex items-center justify-center text-coral-700 text-[11px]"
          >
            <motion.span
              animate={{ rotate: collapsed ? 0 : 180 }}
              transition={{ type: "spring", stiffness: 320, damping: 24 }}
              className="inline-block leading-none"
            >
              ▾
            </motion.span>
          </motion.button>
        )}
      </div>

      <AnimatePresence initial={false}>
        {collapsed && (
          <motion.div
            key="collapsed-summary"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden relative"
          >
            <div className="mt-1.5 text-[13.5px] font-semibold text-ink leading-snug truncate">
              {proposal.event.title}
            </div>
            <div className="text-[11.5px] text-ink-muted mt-0.5 truncate">
              {windowText} · {proposal.event.location}
              {proposal.event.price > 0 ? ` · $${proposal.event.price}` : " · Free"}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence initial={false}>
        {!collapsed && (
          <motion.div
            key="body"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden mt-2"
          >
      <div className="text-[14.5px] leading-snug text-ink relative">
        {proposal.headline ? (
          <span className="block">{proposal.headline}</span>
        ) : (
          <>Y'all are free <b className="text-ink">{windowText}</b>.</>
        )}
        <motion.div
          layout
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
            <span className={proposal.event.price === 0 ? "text-mint font-semibold" : ""}>
              {proposal.event.price === 0 ? "Free" : `$${proposal.event.price}`}
            </span>
          </div>
        </motion.div>
      </div>

      {/* Approval row */}
      {proposal.status === "pending" && (
        <div className="mt-3 flex items-center gap-1.5">
          <span className="text-[10px] uppercase tracking-wider text-ink-muted font-semibold">
            Approvals
          </span>
          <div className="flex -space-x-1">
            {members.map((m) => {
              const ok = proposal.approvals[m.id];
              return (
                <motion.div
                  key={m.id}
                  animate={{ scale: ok ? 1.05 : 1 }}
                  className={`relative w-6 h-6 rounded-full ring-2 ring-cream-50 flex items-center justify-center text-[10px] font-semibold text-white ${
                    ok ? "" : "opacity-40 saturate-50"
                  }`}
                  style={{ background: m.color }}
                  title={`${m.name} ${ok ? "approved" : "waiting"}`}
                >
                  {m.name[0]}
                  {ok && (
                    <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-mint text-white text-[8px] flex items-center justify-center ring-1 ring-cream-50">
                      ✓
                    </span>
                  )}
                </motion.div>
              );
            })}
          </div>
          <span className="ml-auto text-[11px] text-ink-muted">
            {approvedCount}/{totalCount}
          </span>
        </div>
      )}

      <AnimatePresence mode="wait">
        {proposal.status === "pending" && !viewerApproved && (
          <motion.div
            key="action"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="mt-3 grid grid-cols-3 gap-2"
          >
            <motion.button
              whileTap={{ scale: 0.97 }}
              onClick={onApprove}
              className="col-span-2 rounded-full bg-coral-500 text-white text-[13.5px] font-semibold py-2.5 shadow-warm hover:bg-coral-600 transition-colors"
            >
              I'm in
            </motion.button>
            <motion.button
              whileTap={{ scale: 0.97 }}
              onClick={onSkip}
              className="rounded-full bg-white ring-1 ring-ink-faint/50 text-[12px] py-2.5 text-ink-muted font-medium"
            >
              Skip
            </motion.button>
          </motion.div>
        )}

        {proposal.status === "pending" && viewerApproved && (
          <motion.div
            key="waiting"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="mt-3 rounded-2xl bg-coral-50 ring-1 ring-coral-200 px-3 py-2 text-[12.5px] text-coral-700 flex items-center gap-2"
          >
            <span className="w-4 h-4 rounded-full bg-coral-500 text-white flex items-center justify-center text-[10px]">
              ✓
            </span>
            You're in. Waiting on{" "}
            {members
              .filter((m) => !proposal.approvals[m.id])
              .map((m) => m.name)
              .join(" & ") || "the rest"}…
          </motion.div>
        )}

        {proposal.status === "booking" && (
          <motion.div
            key="booking"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <BookingChecklist userNames={members.map((m) => m.name)} onDone={() => {}} />
          </motion.div>
        )}

        {proposal.status === "booked" && (
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
              Booked. <b>Nest is glowing</b> — see you there.
            </span>
          </motion.div>
        )}
      </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
