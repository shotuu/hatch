import { useState } from "react";
import AgentMessage from "./AgentMessage";
import { propose, ProposeResponse } from "./api";

type Msg = {
  id: string;
  author: string;
  color: string;
  text: string;
  ts: string;
};

const SEED_MESSAGES: Msg[] = [
  { id: "m1", author: "Maya", color: "#f472b6", text: "miss y’all", ts: "3 weeks ago" },
  { id: "m2", author: "Jordan", color: "#60a5fa", text: "we gotta do something soon", ts: "3 weeks ago" },
  { id: "m3", author: "Priya", color: "#34d399", text: "yeah for real", ts: "3 weeks ago" },
];

export default function ChatView() {
  const [expiryDays, setExpiryDays] = useState(6);
  const [messages] = useState<Msg[]>(SEED_MESSAGES);
  const [proposal, setProposal] = useState<ProposeResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const onTrigger = async () => {
    setLoading(true);
    const r = await propose();
    setProposal(r);
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-full">
      <header className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold">LA Friends</div>
          <div className="text-[11px] text-neutral-400">Maya · Jordan · Priya · You</div>
        </div>
        <div className="text-[11px] px-2 py-1 rounded-full bg-rose-500/20 text-rose-200 ring-1 ring-rose-400/30">
          Expires in {expiryDays}d
        </div>
      </header>

      <div className="flex-1 overflow-y-auto py-2">
        {proposal && proposal.ok && (
          <AgentMessage
            proposal={proposal}
            onBooked={(d) => setExpiryDays(d)}
          />
        )}

        {messages.map((m) => (
          <div key={m.id} className="px-3 py-1.5">
            <div className="flex items-start gap-2">
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-semibold text-black shrink-0"
                style={{ background: m.color }}
              >
                {m.author[0]}
              </div>
              <div className="min-w-0">
                <div className="text-[11px] text-neutral-400">
                  {m.author} · {m.ts}
                </div>
                <div className="text-sm text-neutral-100 leading-snug">{m.text}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <footer className="p-3 border-t border-white/10 flex gap-2">
        <button
          onClick={onTrigger}
          disabled={loading}
          className="flex-1 rounded-full bg-indigo-500 text-white text-sm font-semibold py-2 disabled:opacity-60"
        >
          {loading ? "Thinking…" : "Trigger agent (demo)"}
        </button>
      </footer>
    </div>
  );
}
