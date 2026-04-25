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
    <div className="px-3 pt-2 pb-1 border-t border-white/5 bg-neutral-950">
      <div className="text-[9px] uppercase tracking-wider text-neutral-600 mb-1.5 px-1">
        Demo controls
      </div>
      <div className="grid grid-cols-3 gap-1.5">
        <button
          onClick={onReactiveDemo}
          disabled={busy}
          className="rounded-lg bg-white/5 ring-1 ring-white/10 text-[10px] py-2 text-neutral-200 disabled:opacity-40 active:scale-95 transition"
        >
          Maya: Lakers msg
        </button>
        <button
          onClick={onProactiveDemo}
          disabled={busy}
          className="rounded-lg bg-indigo-500/30 ring-1 ring-indigo-400/40 text-[10px] py-2 text-indigo-100 disabled:opacity-40 active:scale-95 transition font-semibold"
        >
          Trigger silence
        </button>
        <button
          onClick={onReset}
          disabled={busy}
          className="rounded-lg bg-white/5 ring-1 ring-white/10 text-[10px] py-2 text-neutral-400 disabled:opacity-40 active:scale-95 transition"
        >
          Reset
        </button>
      </div>
    </div>
  );
}
