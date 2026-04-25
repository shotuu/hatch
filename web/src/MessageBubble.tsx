import { motion } from "framer-motion";
import type { User } from "./types";

type Props = {
  author: User;
  text: string;
  ts: string;
  isMe: boolean;
};

const SPRING = { type: "spring" as const, stiffness: 380, damping: 28, mass: 0.8 };

function formatTs(ts: string) {
  // Server emits ISO timestamps; seed messages emit relative strings like "3 weeks ago".
  if (!/^\d/.test(ts)) return ts;
  try {
    const d = new Date(ts);
    const now = Date.now();
    const ageSec = (now - d.getTime()) / 1000;
    if (ageSec < 60) return "now";
    if (ageSec < 3600) return `${Math.round(ageSec / 60)}m`;
    if (ageSec < 86400) return `${Math.round(ageSec / 3600)}h`;
    return d.toLocaleDateString();
  } catch {
    return ts;
  }
}

export default function MessageBubble({ author, text, ts, isMe }: Props) {
  const tsLabel = formatTs(ts);

  if (isMe) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={SPRING}
        className="px-3 py-1 flex flex-col items-end"
      >
        <div className="text-[10px] text-ink-subtle mb-0.5 mr-2">{tsLabel}</div>
        <div className="w-fit max-w-[78%] rounded-[22px] rounded-br-md bg-gradient-to-br from-coral-500 to-coral-400 px-3.5 py-2 text-[15px] leading-snug text-white shadow-bubble break-words">
          {text}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={SPRING}
      className="px-3 py-1 flex items-end gap-2"
    >
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-semibold text-white shrink-0 shadow-bubble"
        style={{ background: author.color }}
      >
        {author.name[0]}
      </div>
      <div className="flex flex-col items-start min-w-0">
        <div className="text-[10px] text-ink-subtle mb-0.5 ml-2">
          {author.name} · {tsLabel}
        </div>
        <div className="w-fit max-w-[260px] rounded-[22px] rounded-bl-md bg-white px-3.5 py-2 text-[15px] leading-snug text-ink shadow-bubble ring-1 ring-ink-faint/30 break-words">
          {text}
        </div>
      </div>
    </motion.div>
  );
}
