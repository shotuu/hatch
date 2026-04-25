import { motion } from "framer-motion";
import type { User } from "./types";

type Props = {
  author: User;
  text: string;
  ts: string;
  isMe: boolean;
};

const SPRING = { type: "spring" as const, stiffness: 380, damping: 28, mass: 0.8 };

export default function MessageBubble({ author, text, ts, isMe }: Props) {
  if (isMe) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={SPRING}
        className="px-3 py-1 flex flex-col items-end"
      >
        <div className="text-[10px] text-ink-subtle mb-0.5 mr-2">{ts}</div>
        <div className="max-w-[78%] rounded-[22px] rounded-br-md bg-gradient-to-br from-coral-500 to-coral-400 px-3.5 py-2 text-[15px] leading-snug text-white shadow-bubble">
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
      <div className="flex flex-col">
        <div className="text-[10px] text-ink-subtle mb-0.5 ml-2">
          {author.name} · {ts}
        </div>
        <div className="max-w-[260px] rounded-[22px] rounded-bl-md bg-white px-3.5 py-2 text-[15px] leading-snug text-ink shadow-bubble ring-1 ring-ink-faint/30">
          {text}
        </div>
      </div>
    </motion.div>
  );
}
