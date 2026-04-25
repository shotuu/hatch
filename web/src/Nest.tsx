import { motion } from "framer-motion";

export type NestTier = {
  emoji: string;
  label: string;
  pillStyle: string;
  barStyle: string;
  ringStyle: string;
};

export const NEST_MAX = 30;

export function nestTier(warmth: number): NestTier {
  if (warmth >= 22) {
    return {
      emoji: "✨",
      label: "Nest is glowing",
      pillStyle: "bg-mint/15 text-[#2F8F5A] ring-mint/30",
      barStyle: "bg-mint",
      ringStyle: "ring-mint/40",
    };
  }
  if (warmth >= 12) {
    return {
      emoji: "🪺",
      label: "Nest is warm",
      pillStyle: "bg-yolk/20 text-coral-700 ring-yolk/40",
      barStyle: "bg-yolk",
      ringStyle: "ring-yolk/50",
    };
  }
  if (warmth >= 5) {
    return {
      emoji: "🥚",
      label: "Nest is cooling",
      pillStyle: "bg-coral-100 text-coral-700 ring-coral-200",
      barStyle: "bg-coral-400",
      ringStyle: "ring-coral-200",
    };
  }
  return {
    emoji: "🥚",
    label: "Nest is cold — let's hatch something",
    pillStyle: "bg-coral-100 text-coral-700 ring-coral-200",
    barStyle: "bg-coral-500",
    ringStyle: "ring-coral-300",
  };
}

function pct(warmth: number, max = NEST_MAX) {
  return Math.max(0, Math.min(100, (warmth / max) * 100));
}

/** Header meter — pill label + thin progress bar. */
export function NestMeter({ warmth, max = NEST_MAX }: { warmth: number; max?: number }) {
  const tier = nestTier(warmth);
  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15, duration: 0.4 }}
      className="mt-2 mx-auto flex flex-col items-center gap-1"
    >
      <div className={`text-[10.5px] font-semibold px-2.5 py-1 rounded-full ring-1 ${tier.pillStyle}`}>
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
          initial={false}
          animate={{ width: `${pct(warmth, max)}%` }}
          transition={{ type: "spring", stiffness: 120, damping: 22 }}
        />
      </div>
    </motion.div>
  );
}

/** Compact row indicator — egg + tiny vertical bar, sits at the right of a chat row. */
export function NestEgg({ warmth, max = NEST_MAX }: { warmth: number; max?: number }) {
  const tier = nestTier(warmth);
  const fill = pct(warmth, max);
  return (
    <div
      className="flex items-center gap-1 shrink-0"
      title={`${tier.label} (${warmth}/${max})`}
      aria-label={`${tier.label}, ${warmth} of ${max}`}
    >
      <span className="text-[14px] leading-none">{tier.emoji}</span>
      <div className="relative w-1.5 h-6 rounded-full bg-cream-200 overflow-hidden">
        <motion.div
          className={`absolute bottom-0 left-0 right-0 ${tier.barStyle}`}
          initial={false}
          animate={{ height: `${fill}%` }}
          transition={{ type: "spring", stiffness: 140, damping: 22 }}
        />
      </div>
    </div>
  );
}
