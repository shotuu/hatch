import { motion } from "framer-motion";

type Props = {
  onReactiveDemo: () => void;
  onProactiveDemo: () => void;
  onReset: () => void;
  busy: boolean;
};

export default function DemoControls({
  onReactiveDemo,
  onProactiveDemo,
  onReset,
  busy,
}: Props) {
  return (
    <div className="px-3 pt-2 pb-2 border-t border-ink-faint/40 bg-cream-100">
      <div className="text-[9px] uppercase tracking-wider text-ink-subtle mb-1.5 px-1 flex items-center gap-1">
        <span className="w-1.5 h-1.5 rounded-full bg-coral-500 animate-pulse" />
        Demo controls
      </div>
      <div className="grid grid-cols-3 gap-1.5">
        <Btn onClick={onReactiveDemo} busy={busy} variant="ghost">
          Maya: Lakers msg
        </Btn>
        <Btn onClick={onProactiveDemo} busy={busy} variant="primary">
          Trigger silence
        </Btn>
        <Btn onClick={onReset} busy={busy} variant="ghost">
          Reset
        </Btn>
      </div>
    </div>
  );
}

function Btn({
  children,
  onClick,
  busy,
  variant,
}: {
  children: React.ReactNode;
  onClick: () => void;
  busy: boolean;
  variant: "primary" | "ghost";
}) {
  const base =
    "rounded-lg text-[10px] py-2 font-semibold disabled:opacity-40 transition-colors";
  const cls =
    variant === "primary"
      ? `${base} bg-coral-500 text-white hover:bg-coral-600`
      : `${base} bg-white ring-1 ring-ink-faint/50 text-ink-muted hover:text-ink`;
  return (
    <motion.button
      whileTap={{ scale: 0.96 }}
      onClick={onClick}
      disabled={busy}
      className={cls}
    >
      {children}
    </motion.button>
  );
}
