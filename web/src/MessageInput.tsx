import { motion } from "framer-motion";
import { KeyboardEvent, useState } from "react";

type Props = {
  viewerName: string;
  onSend: (text: string) => Promise<void> | void;
  disabled?: boolean;
};

export default function MessageInput({ viewerName, onSend, disabled }: Props) {
  const [text, setText] = useState("");
  const canSend = text.trim().length > 0 && !disabled;

  const submit = async () => {
    if (!canSend) return;
    const t = text.trim();
    setText("");
    await onSend(t);
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="px-3 pt-2 pb-3 flex items-end gap-2 border-t border-ink-faint/40 bg-cream-50">
      <button
        className="w-9 h-9 rounded-full bg-cream-200 flex items-center justify-center text-ink-muted shrink-0"
        title="(unimplemented)"
      >
        +
      </button>
      <div className="flex-1 rounded-3xl bg-white ring-1 ring-ink-faint/50 px-3 py-1.5 shadow-bubble flex items-center">
        <textarea
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKey}
          placeholder={`Message as ${viewerName}…`}
          disabled={disabled}
          className="flex-1 bg-transparent resize-none outline-none text-[14px] text-ink placeholder:text-ink-subtle max-h-24 leading-snug py-1"
        />
      </div>
      <motion.button
        whileTap={{ scale: 0.92 }}
        onClick={submit}
        disabled={!canSend}
        className={`w-9 h-9 rounded-full flex items-center justify-center text-white shadow-warm shrink-0 transition-colors ${
          canSend ? "bg-coral-500" : "bg-ink-faint"
        }`}
      >
        ↑
      </motion.button>
    </div>
  );
}
