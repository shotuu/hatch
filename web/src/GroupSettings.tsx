import { AnimatePresence, motion } from "framer-motion";
import { useState, type ReactNode } from "react";
import type { User } from "./types";

type Props = {
  open: boolean;
  tripName: string;
  members: User[];
  onClose: () => void;
};

export default function GroupSettings({ open, tripName, members, onClose }: Props) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-ink/30 z-40"
          />
          <motion.aside
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 360, damping: 38 }}
            className="absolute inset-0 bg-cream-50 z-50 shadow-warmlg flex flex-col"
          >
            <header className="px-4 pt-12 pb-2 flex items-center justify-between">
              <button
                onClick={onClose}
                className="text-coral-600 text-[22px] leading-none px-1 -ml-1"
                aria-label="Back"
              >
                ‹
              </button>
              <div className="text-[12px] uppercase tracking-wider text-ink-muted font-semibold">
                Group info
              </div>
              <span className="w-6" />
            </header>

            <div className="flex-1 overflow-y-auto no-scrollbar pb-6">
              <div className="px-4 pt-3 pb-5 flex flex-col items-center text-center">
                <div className="flex -space-x-2 mb-3">
                  {members.map((m) => (
                    <div
                      key={m.id}
                      className="w-12 h-12 rounded-full ring-2 ring-cream-50 flex items-center justify-center text-[16px] font-semibold text-white shadow-bubble"
                      style={{ background: m.color }}
                    >
                      {m.name[0]}
                    </div>
                  ))}
                </div>
                <div className="text-[20px] font-semibold text-ink leading-tight">
                  {tripName}
                </div>
                <div className="text-[11.5px] text-ink-subtle mt-1">
                  {members.length} members · {members.map((m) => m.name).join(", ")}
                </div>
              </div>

              <div className="px-4 grid grid-cols-4 gap-2 mb-6">
                <QuickAction icon={<IconUserPlus />} label="Add" />
                <QuickAction icon={<IconSearch />} label="Search" />
                <QuickAction icon={<IconBell />} label="Mute" />
                <QuickAction icon={<IconDots />} label="Options" />
              </div>

              <Section>
                <LocationRow />
                <Row icon={<IconPalette />} label="Themes" hint="Cream & coral" />
                <Row icon={<IconLink />} label="Invite link" hint="hatch.app/la-friends" />
                <Row icon={<IconShield />} label="Privacy & safety" />
                <Row icon={<IconBell />} label="Notifications" hint="All messages" />
              </Section>

              <Section>
                <Row icon={<IconStar />} label="Starred messages" />
                <Row icon={<IconImage />} label="Media, files & links" />
              </Section>

              <Section>
                <Row icon={<IconPlus />} label="Create a new groupchat" emphasis="coral" />
                <Row icon={<IconLogout />} label="Leave group" emphasis="danger" />
              </Section>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

function QuickAction({ icon, label }: { icon: ReactNode; label: string }) {
  return (
    <motion.button
      whileTap={{ scale: 0.94 }}
      className="flex flex-col items-center gap-1.5 rounded-2xl bg-white ring-1 ring-ink-faint/40 py-3 shadow-bubble"
    >
      <span className="w-8 h-8 rounded-full bg-coral-50 ring-1 ring-coral-200/70 text-coral-600 flex items-center justify-center">
        {icon}
      </span>
      <span className="text-[11px] font-medium text-ink-muted">{label}</span>
    </motion.button>
  );
}

function LocationRow() {
  const [location, setLocation] = useState("Los Angeles, CA");
  const [editing, setEditing] = useState(false);
  return (
    <div className="px-3.5 py-3 flex items-center gap-3">
      <span className="w-8 h-8 rounded-xl flex items-center justify-center ring-1 bg-coral-50 text-coral-600 ring-coral-200/70 shrink-0">
        <IconPin />
      </span>
      <div className="flex-1 min-w-0">
        <div className="text-[13.5px] font-medium text-ink leading-tight">Location</div>
        {editing ? (
          <input
            autoFocus
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            onBlur={() => setEditing(false)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === "Escape") {
                (e.target as HTMLInputElement).blur();
              }
            }}
            placeholder="Where should plans happen?"
            className="mt-0.5 w-full bg-transparent border-b border-coral-300 text-[12px] text-ink-muted focus:outline-none focus:border-coral-500 placeholder:text-ink-faint"
          />
        ) : (
          <button
            onClick={() => setEditing(true)}
            className="mt-0.5 text-[11.5px] text-ink-subtle truncate text-left w-full hover:text-ink-muted"
          >
            {location || "Tap to set where plans should happen"}
          </button>
        )}
      </div>
      <button
        onClick={() => setEditing((v) => !v)}
        className="text-[11px] font-medium text-coral-600 px-2 py-1 rounded-md hover:bg-coral-50"
      >
        {editing ? "Done" : "Edit"}
      </button>
    </div>
  );
}

function Section({ children }: { children: ReactNode }) {
  return (
    <div className="mx-4 mb-4 rounded-2xl bg-white ring-1 ring-ink-faint/40 overflow-hidden divide-y divide-ink-faint/30 shadow-bubble">
      {children}
    </div>
  );
}

function Row({
  icon,
  label,
  hint,
  emphasis,
}: {
  icon: ReactNode;
  label: string;
  hint?: string;
  emphasis?: "coral" | "danger";
}) {
  const labelColor =
    emphasis === "danger"
      ? "text-[#B4322B]"
      : emphasis === "coral"
        ? "text-coral-600"
        : "text-ink";
  const iconBg =
    emphasis === "danger"
      ? "bg-[#FBE5E2] text-[#B4322B] ring-[#F2BCB6]"
      : emphasis === "coral"
        ? "bg-coral-50 text-coral-600 ring-coral-200/70"
        : "bg-cream-100 text-ink-muted ring-ink-faint/40";
  return (
    <motion.button
      whileTap={{ scale: 0.985 }}
      className="w-full flex items-center gap-3 px-3.5 py-3 text-left hover:bg-cream-100/50 transition-colors"
    >
      <span className={`w-8 h-8 rounded-xl flex items-center justify-center ring-1 ${iconBg}`}>
        {icon}
      </span>
      <span className="flex-1 min-w-0">
        <span className={`block text-[13.5px] font-medium ${labelColor}`}>{label}</span>
        {hint && (
          <span className="block text-[11px] text-ink-subtle truncate">{hint}</span>
        )}
      </span>
      <span className="text-ink-faint text-[16px] leading-none">›</span>
    </motion.button>
  );
}

const stroke = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.7,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

function IconUserPlus() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" {...stroke}>
      <circle cx="10" cy="8" r="3.5" />
      <path d="M3.5 19c.8-3.2 3.5-5 6.5-5s5.7 1.8 6.5 5" />
      <path d="M19 8v6M16 11h6" />
    </svg>
  );
}
function IconSearch() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" {...stroke}>
      <circle cx="11" cy="11" r="6" />
      <path d="m20 20-4.3-4.3" />
    </svg>
  );
}
function IconBell() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" {...stroke}>
      <path d="M6 16h12l-1.5-2V10a4.5 4.5 0 0 0-9 0v4L6 16Z" />
      <path d="M10 19a2 2 0 0 0 4 0" />
    </svg>
  );
}
function IconDots() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <circle cx="6" cy="12" r="1.6" />
      <circle cx="12" cy="12" r="1.6" />
      <circle cx="18" cy="12" r="1.6" />
    </svg>
  );
}
function IconPin() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" {...stroke}>
      <path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 1 1 13 0c0 5-6.5 11-6.5 11Z" />
      <circle cx="12" cy="10" r="2.3" />
    </svg>
  );
}
function IconPalette() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" {...stroke}>
      <path d="M12 4a8 8 0 1 0 0 16c1.2 0 1.5-1 1-1.8-.6-.9 0-2.2 1.2-2.2H17a3 3 0 0 0 3-3A8 8 0 0 0 12 4Z" />
      <circle cx="8" cy="11" r=".9" fill="currentColor" />
      <circle cx="11" cy="8" r=".9" fill="currentColor" />
      <circle cx="15" cy="9" r=".9" fill="currentColor" />
    </svg>
  );
}
function IconLink() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" {...stroke}>
      <path d="M10 14a3.5 3.5 0 0 0 5 0l3-3a3.5 3.5 0 0 0-5-5l-1 1" />
      <path d="M14 10a3.5 3.5 0 0 0-5 0l-3 3a3.5 3.5 0 0 0 5 5l1-1" />
    </svg>
  );
}
function IconShield() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" {...stroke}>
      <path d="M12 4 5 7v6c0 4 3 6.5 7 7 4-.5 7-3 7-7V7l-7-3Z" />
    </svg>
  );
}
function IconStar() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" {...stroke}>
      <path d="m12 4 2.4 5 5.6.8-4 3.9.9 5.5L12 16.6 7.1 19.2l1-5.5-4-3.9 5.5-.8L12 4Z" />
    </svg>
  );
}
function IconImage() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" {...stroke}>
      <rect x="4" y="5" width="16" height="14" rx="2" />
      <circle cx="9" cy="10" r="1.4" />
      <path d="m4.5 17 4.5-4 5 4.5 2.5-2 3 2.5" />
    </svg>
  );
}
function IconPlus() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" {...stroke}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}
function IconLogout() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" {...stroke}>
      <path d="M14 5h4a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1h-4" />
      <path d="M10 8 6 12l4 4M6 12h10" />
    </svg>
  );
}
