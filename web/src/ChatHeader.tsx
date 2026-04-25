import { motion } from "framer-motion";
import HatchLogo from "./HatchLogo";
import type { User } from "./types";

type Props = {
  tripName: string;
  members: User[];
  expiryDays: number;
  onOpenIdeas: () => void;
  ideasCount: number;
};

export default function ChatHeader({
  tripName,
  members,
  expiryDays,
  onOpenIdeas,
  ideasCount,
}: Props) {
  const expiryStyle =
    expiryDays <= 7
      ? "bg-coral-100 text-coral-700 ring-coral-200"
      : expiryDays <= 14
      ? "bg-yolk/20 text-coral-700 ring-yolk/40"
      : "bg-mint/15 text-[#2F8F5A] ring-mint/30";

  return (
    <header className="px-4 pt-2 pb-3 border-b border-ink-faint/40 bg-cream-50/95 backdrop-blur sticky top-0 z-10">
      <div className="flex items-center justify-between">
        <button className="text-coral-600 text-[15px] font-medium px-1 -ml-1">
          ‹
        </button>

        <div className="flex flex-col items-center">
          <div className="flex -space-x-2 mb-1">
            {members.map((m) => (
              <div
                key={m.id}
                className="w-7 h-7 rounded-full ring-2 ring-cream-50 flex items-center justify-center text-[11px] font-semibold text-white shadow-bubble"
                style={{ background: m.color }}
              >
                {m.name[0]}
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

      <motion.div
        initial={{ opacity: 0, y: -4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15, duration: 0.4 }}
        className={`mt-2 mx-auto w-fit text-[10.5px] font-semibold px-2.5 py-1 rounded-full ring-1 ${expiryStyle}`}
      >
        {expiryDays <= 7 ? "🥚 " : ""}
        {expiryDays} day{expiryDays === 1 ? "" : "s"} left to plan something
      </motion.div>
    </header>
  );
}
