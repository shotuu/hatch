import { AnimatePresence, motion } from "framer-motion";
import HatchLogo from "./HatchLogo";
import type { HatchState } from "./state";

type Props = Pick<
  HatchState,
  | "busy"
  | "wipeStatus"
  | "triggerProactive"
  | "triggerReactive"
  | "reset"
  | "onWipe"
>;

export default function DemoPanel({
  busy,
  wipeStatus,
  triggerProactive,
  triggerReactive,
  reset,
  onWipe,
}: Props) {
  return (
    <aside className="w-[260px] shrink-0 rounded-3xl bg-cream-50 ring-1 ring-ink-faint/40 shadow-warmlg p-5 flex flex-col gap-5 self-start mt-12">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <HatchLogo size={20} />
          <div>
            <div className="text-[13px] font-semibold text-ink leading-tight">
              Hatch
            </div>
            <div className="text-[10px] text-ink-subtle uppercase tracking-wider">
              dev console
            </div>
          </div>
        </div>
        <span className="w-2 h-2 rounded-full bg-mint shadow-[0_0_0_3px_rgba(91,197,134,0.18)]" />
      </header>

      <Section title="Demo flows">
        <PrimaryBtn onClick={triggerProactive} busy={busy}>
          Trigger silence
        </PrimaryBtn>
        <GhostBtn onClick={triggerReactive} busy={busy}>
          Send Jono's Lakers msg
        </GhostBtn>
      </Section>

      <Section title="Chat state">
        <GhostBtn onClick={reset} busy={busy}>
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

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
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

function PrimaryBtn({
  children,
  onClick,
  busy,
}: {
  children: React.ReactNode;
  onClick: () => void;
  busy: boolean;
}) {
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

function GhostBtn({
  children,
  onClick,
  busy,
}: {
  children: React.ReactNode;
  onClick: () => void;
  busy: boolean;
}) {
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

function DangerBtn({
  children,
  onClick,
  busy,
}: {
  children: React.ReactNode;
  onClick: () => void;
  busy: boolean;
}) {
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
