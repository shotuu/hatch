import { useEffect, useState } from "react";

type Props = {
  userNames: string[];
  onDone: () => void;
};

export default function BookingChecklist({ userNames, onDone }: Props) {
  const steps = [
    "Reserved spot",
    ...userNames.map((n) => `Added to ${n}'s calendar`),
  ];
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (current >= steps.length) {
      const t = setTimeout(onDone, 600);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setCurrent((c) => c + 1), 450);
    return () => clearTimeout(t);
  }, [current, steps.length, onDone]);

  return (
    <ul className="mt-3 space-y-1.5">
      {steps.map((s, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <li
            key={s}
            className={`flex items-center gap-2 text-[13px] transition-all duration-300 ${
              done
                ? "text-emerald-300"
                : active
                ? "text-neutral-100"
                : "text-neutral-600"
            }`}
          >
            <span
              className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] transition-all ${
                done
                  ? "bg-emerald-400/20 ring-1 ring-emerald-400/60"
                  : active
                  ? "bg-white/10 ring-1 ring-white/30 animate-pulse"
                  : "bg-white/5 ring-1 ring-white/10"
              }`}
            >
              {done ? "✓" : ""}
            </span>
            {s}
          </li>
        );
      })}
    </ul>
  );
}
