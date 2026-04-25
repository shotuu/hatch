import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import HatchLogo from "./HatchLogo";
import { nestTier, NEST_MAX } from "./Nest";
import type { GroupActions } from "./state";

type Props = {
  actions: GroupActions;
};

export default function DemoPanel({ actions }: Props) {
  const {
    busy,
    wipeStatus,
    triggerProactive,
    demoLakers,
    reset,
    onWipe,
    setWarmth,
    snapshot,
  } = actions;
  const warmth = snapshot.expiry_days;
  const tier = nestTier(warmth);

  const [autoDecay, setAutoDecay] = useState(false);
  const [decayRateMs, setDecayRateMs] = useState(2000);
  const warmthRef = useRef(warmth);
  warmthRef.current = warmth;

  useEffect(() => {
    if (!autoDecay) return;
    const id = setInterval(() => {
      const next = warmthRef.current - 1;
      if (next < 0) {
        setAutoDecay(false);
        return;
      }
      setWarmth(next);
    }, decayRateMs);
    return () => clearInterval(id);
  }, [autoDecay, decayRateMs, setWarmth]);
  return (
    <aside className="w-[260px] shrink-0 rounded-3xl bg-cream-50 ring-1 ring-ink-faint/40 shadow-warmlg p-5 flex flex-col gap-5 self-start mt-12">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <HatchLogo size={20} />
          <div>
            <div className="text-[13px] font-semibold text-ink leading-tight">Hatch</div>
            <div className="text-[10px] text-ink-subtle uppercase tracking-wider">
              dev console
            </div>
          </div>
        </div>
        <span className="w-2 h-2 rounded-full bg-mint shadow-[0_0_0_3px_rgba(91,197,134,0.18)]" />
      </header>

      <Section title="Demo flows">
        <PrimaryBtn onClick={() => triggerProactive()} busy={busy}>
          Trigger silence
        </PrimaryBtn>
        <GhostBtn onClick={() => demoLakers()} busy={busy}>
          Send Jono's Lakers msg
        </GhostBtn>
      </Section>

      <Section title="Time controls">
        <div className="rounded-xl bg-white ring-1 ring-ink-faint/40 p-3 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-[12px] text-ink">
              <span className="text-[14px] leading-none">{tier.emoji}</span>
              <span className="font-semibold">{tier.label}</span>
            </div>
            <div className="font-mono text-[11px] text-ink-muted tabular-nums">
              {warmth}/{NEST_MAX}
            </div>
          </div>

          <input
            type="range"
            min={0}
            max={NEST_MAX}
            value={warmth}
            disabled={busy}
            onChange={(e) => setWarmth(Number(e.target.value))}
            aria-label="Nest warmth"
            className="w-full accent-coral-500"
          />

          <div className="flex gap-1.5">
            <StepBtn onClick={() => setWarmth(Math.max(0, warmth - 1))} busy={busy}>
              −1 day
            </StepBtn>
            <StepBtn onClick={() => setWarmth(Math.max(0, warmth - 5))} busy={busy}>
              −5 days
            </StepBtn>
            <StepBtn onClick={() => setWarmth(NEST_MAX)} busy={busy}>
              Restore
            </StepBtn>
          </div>

          <label className="flex items-center justify-between gap-2 text-[12px] text-ink-muted cursor-pointer">
            <span className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={autoDecay}
                onChange={(e) => setAutoDecay(e.target.checked)}
                className="accent-coral-500"
              />
              <span>Auto-decay</span>
            </span>
            <select
              value={decayRateMs}
              onChange={(e) => setDecayRateMs(Number(e.target.value))}
              className="text-[11px] bg-cream-50 ring-1 ring-ink-faint/40 rounded-md px-1.5 py-0.5"
            >
              <option value={1000}>1s</option>
              <option value={2000}>2s</option>
              <option value={5000}>5s</option>
            </select>
          </label>

          <div className="text-[10.5px] text-ink-subtle leading-snug">
            When warmth drops to <b>≤3</b>, the agent auto-fires its pinned proposal — same as <i>Trigger silence</i>.
          </div>
        </div>
      </Section>

      <Section title="Chat state">
        <GhostBtn onClick={() => reset()} busy={busy}>
          Reset chat
        </GhostBtn>
      </Section>

      <Section title="Calendars">
        <DangerBtn onClick={onWipe} busy={busy}>
          Wipe Hatch events
        </DangerBtn>
        <AnimatePresence>
          {wipeStatus && (
            <motion.div
              key={wipeStatus}
              initial={{ opacity: 0, y: -2 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="text-[11px] text-mint font-semibold mt-1.5 flex items-center gap-1.5"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-mint" />
              {wipeStatus}
            </motion.div>
          )}
        </AnimatePresence>
      </Section>

      <footer className="mt-auto pt-3 border-t border-ink-faint/40 text-[10px] text-ink-subtle leading-relaxed">
        <div>
          <span className="text-ink-muted font-mono">localhost:8000</span>
        </div>
        <div className="mt-1">Hide before live demo.</div>
      </footer>
    </aside>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-ink-subtle font-semibold mb-2">
        {title}
      </div>
      <div className="flex flex-col gap-1.5">{children}</div>
    </div>
  );
}

const baseBtn =
  "rounded-xl text-[13px] font-semibold py-2.5 px-3 disabled:opacity-40 transition-colors w-full text-left";

function PrimaryBtn({ children, onClick, busy }: { children: React.ReactNode; onClick: () => void; busy: boolean }) {
  return (
    <motion.button
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      disabled={busy}
      className={`${baseBtn} bg-coral-500 text-white hover:bg-coral-600 shadow-warm flex items-center justify-between`}
    >
      <span>{children}</span>
      <span>→</span>
    </motion.button>
  );
}

function GhostBtn({ children, onClick, busy }: { children: React.ReactNode; onClick: () => void; busy: boolean }) {
  return (
    <motion.button
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      disabled={busy}
      className={`${baseBtn} bg-white ring-1 ring-ink-faint/50 text-ink-muted hover:text-ink hover:ring-ink-faint`}
    >
      {children}
    </motion.button>
  );
}

function StepBtn({ children, onClick, busy }: { children: React.ReactNode; onClick: () => void; busy: boolean }) {
  return (
    <motion.button
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      disabled={busy}
      className="flex-1 rounded-lg bg-cream-100 ring-1 ring-ink-faint/40 text-[11px] font-medium text-ink-muted py-1.5 hover:text-ink hover:bg-cream-200 disabled:opacity-40 transition-colors"
    >
      {children}
    </motion.button>
  );
}

function DangerBtn({ children, onClick, busy }: { children: React.ReactNode; onClick: () => void; busy: boolean }) {
  return (
    <motion.button
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      disabled={busy}
      className={`${baseBtn} bg-white ring-1 ring-coral-300 text-coral-600 hover:bg-coral-50`}
    >
      {children}
    </motion.button>
  );
}
