import { motion } from "framer-motion";
import { useEffect, useState } from "react";

type Props = {
  userNames: string[];
  onDone: () => void;
};

export default function BookingChecklist({ userNames, onDone }: Props) {
  const steps = [
    "Reserved your spot",
    ...userNames.map((n) => `Added to ${n}'s calendar`),
  ];
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (current >= steps.length) {
      const t = setTimeout(onDone, 500);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setCurrent((c) => c + 1), 420);
    return () => clearTimeout(t);
  }, [current, steps.length, onDone]);

  return (
    <ul className="mt-3 space-y-1.5">
      {steps.map((s, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <motion.li
            key={s}
            initial={{ opacity: 0, x: -4 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className={`flex items-center gap-2 text-[13px] transition-colors duration-300 ${
              done ? "text-mint" : active ? "text-ink" : "text-ink-subtle"
            }`}
          >
            <span
              className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] transition-all ${
                done
                  ? "bg-mint text-white animate-tick-pop"
                  : active
                  ? "bg-coral-100 ring-1 ring-coral-300 animate-pulse"
                  : "bg-cream-200 ring-1 ring-ink-faint/40"
              }`}
            >
              {done ? "✓" : ""}
            </span>
            {s}
          </motion.li>
        );
      })}
    </ul>
  );
}
