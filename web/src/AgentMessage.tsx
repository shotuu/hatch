import { useState } from "react";
import { book, ProposeResponse } from "./api";

type Props = {
  proposal: Extract<ProposeResponse, { ok: true }>;
  onBooked: (days: number) => void;
};

export default function AgentMessage({ proposal, onBooked }: Props) {
  const [state, setState] = useState<"idle" | "booking" | "booked">("idle");

  const start = new Date(proposal.window.start);
  const end = new Date(proposal.window.end);
  const windowText = `${start.toLocaleDateString(undefined, { weekday: "short" })} ${start.toLocaleTimeString([], { hour: "numeric" })}–${end.toLocaleTimeString([], { hour: "numeric" })}`;

  const onBook = async () => {
    setState("booking");
    const resp = await book(proposal.event.id);
    if (resp.ok) {
      setState("booked");
      onBooked(resp.expiry_reset_days ?? 30);
    } else {
      setState("idle");
    }
  };

  return (
    <div className="mx-3 my-2 rounded-2xl bg-gradient-to-br from-indigo-500/15 to-fuchsia-500/10 ring-1 ring-indigo-400/30 p-3">
      <div className="text-[11px] uppercase tracking-wider text-indigo-300/80 mb-1">
        Plans agent · pinned
      </div>
      <div className="text-sm leading-snug text-neutral-100">
        This chat expires soon. You’re all free <b>{windowText}</b>.{" "}
        <b>{proposal.event.title}</b> at {proposal.event.location}. Want me to
        set it up?
      </div>

      {state === "booked" ? (
        <div className="mt-3 text-xs text-emerald-300">
          Done. Added to 4 calendars. Expiry reset — 30 days.
        </div>
      ) : (
        <div className="mt-3 flex gap-2">
          <button
            disabled={state === "booking"}
            onClick={onBook}
            className="flex-1 rounded-full bg-white text-black text-sm font-semibold py-2 disabled:opacity-60"
          >
            {state === "booking" ? "Booking…" : "Book it"}
          </button>
          <button className="flex-1 rounded-full bg-white/5 ring-1 ring-white/10 text-sm py-2">
            Something else
          </button>
        </div>
      )}
    </div>
  );
}
