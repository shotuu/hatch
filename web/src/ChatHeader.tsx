import { motion } from "framer-motion";
import HatchLogo from "./HatchLogo";
import { NestMeter } from "./Nest";
import type { User } from "./types";

type Props = {
  tripName: string;
  members: User[];
  nestWarmth: number;
  nestMax: number;
  onOpenIdeas: () => void;
  ideasCount: number;
  onBack?: () => void;
};

type NestTier = {
  emoji: string;
  label: string;
  pillStyle: string;
  barStyle: string;
};

function nestTier(warmth: number): NestTier {
  if (warmth >= 22) {
    return {
      emoji: "✨",
      label: "Nest is glowing",
      pillStyle: "bg-mint/15 text-[#2F8F5A] ring-mint/30",
      barStyle: "bg-mint",
    };
  }
  if (warmth >= 12) {
    return {
      emoji: "🪺",
      label: "Nest is warm",
      pillStyle: "bg-yolk/20 text-coral-700 ring-yolk/40",
      barStyle: "bg-yolk",
    };
  }
  if (warmth >= 5) {
    return {
      emoji: "🥚",
      label: "Nest is cooling",
      pillStyle: "bg-coral-100 text-coral-700 ring-coral-200",
      barStyle: "bg-coral-400",
    };
  }
  return {
    emoji: "🥚",
    label: "Nest is cold — let's hatch something",
    pillStyle: "bg-coral-100 text-coral-700 ring-coral-200",
    barStyle: "bg-coral-500",
  };
}

export default function ChatHeader({
  tripName,
  members,
  nestWarmth,
  nestMax,
  onOpenIdeas,
  ideasCount,
  onBack,
}: Props) {
  return (
    <header className="px-4 pt-2 pb-3 border-b border-ink-faint/40 bg-cream-50/95 backdrop-blur sticky top-0 z-10">
      <div className="flex items-center justify-between">
        <motion.button
          whileTap={{ scale: 0.92 }}
          onClick={onBack}
          aria-label="Back to chats"
          className="text-coral-600 text-[22px] leading-none font-medium px-1 -ml-1"
        >
          ‹
        </motion.button>

        <div className="flex flex-col items-center">
          <div className="flex -space-x-2 mb-1">
            {members.map((m) => (
              <div key={m.id} className="relative">
                <div
                  className="w-7 h-7 rounded-full ring-2 ring-cream-50 flex items-center justify-center text-[11px] font-semibold text-white shadow-bubble"
                  style={{ background: m.color }}
                >
                  {m.name[0]}
                </div>
                <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-mint ring-2 ring-cream-50" />
              </div>
            ))}
          </div>
          <div className="text-[14px] font-semibold text-ink">{tripName}</div>
          <div className="text-[10px] text-ink-subtle">
            {members.map((m) => m.name).join(" · ")}
          </div>
        </div>

        <motion.button
          whileTap={{ scale: 0.92 }}
          onClick={onOpenIdeas}
          className="relative p-1"
          aria-label="Open ideas panel"
        >
          <HatchLogo size={20} />
          {ideasCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 min-w-[14px] h-[14px] px-1 rounded-full bg-coral-500 text-white text-[9px] font-semibold flex items-center justify-center ring-2 ring-cream-50">
              {ideasCount}
            </span>
          )}
        </motion.button>
      </div>

      <NestMeter warmth={expiryDays} />
    </header>
  );
}

function NestMeter({ warmth, max }: { warmth: number; max: number }) {
  const tier = nestTier(warmth);
  const pct = Math.max(0, Math.min(100, (warmth / max) * 100));
  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15, duration: 0.4 }}
      className="mt-2 mx-auto flex flex-col items-center gap-1"
    >
      <div
        className={`text-[10.5px] font-semibold px-2.5 py-1 rounded-full ring-1 ${tier.pillStyle}`}
      >
        {tier.emoji} {tier.label}
      </div>
      <div
        className="w-28 h-1 rounded-full bg-cream-200 overflow-hidden"
        role="progressbar"
        aria-label="Nest warmth"
        aria-valuenow={warmth}
        aria-valuemin={0}
        aria-valuemax={max}
      >
        <motion.div
          className={`h-full ${tier.barStyle}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ type: "spring", stiffness: 120, damping: 22 }}
        />
      </div>
    </motion.div>
  );
}
