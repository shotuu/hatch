import { motion } from "framer-motion";
import HatchLogo from "./HatchLogo";
import { NestMeter } from "./Nest";
import type { User } from "./types";

type Props = {
  tripName: string;
  members: User[];
  expiryDays: number;
  onOpenIdeas: () => void;
  ideasCount: number;
  onBack?: () => void;
};

export default function ChatHeader({
  tripName,
  members,
  expiryDays,
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

      <NestMeter warmth={expiryDays} />
    </header>
  );
}
