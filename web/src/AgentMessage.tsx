import { useState } from "react";
import { book, ProposeResponse } from "./api";
import BookingChecklist from "./BookingChecklist";

type Props = {
  proposal: Extract<ProposeResponse, { ok: true }>;
  onBooked: (days: number) => void;
};

function formatWindow(startISO: string, endISO: string) {
  const s = new Date(startISO);
  const e = new Date(endISO);
  const day = s.toLocaleDateString(undefined, { weekday: "long" });
  const fmt = (d: Date) =>
    d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  return `${day} ${fmt(s)}–${fmt(e)}`;
}

export default function AgentMessage({ proposal, onBooked }: Props) {
  const [state, setState] = useState<"idle" | "booking" | "booked">("idle");
  const windowText = formatWindow(proposal.window.start, proposal.window.end);
  const userNames = proposal.users.map((u) => u.name);

  const onBook = async () => {
    setState("booking");
    await book(proposal.event.id);
  };

  const onChecklistDone = () => {
    setState("booked");
    onBooked(30);
  };

  const eventTime = new Date(proposal.event.datetime).toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  });

  return (
    <div className="mx-3 my-3 rounded-2xl bg-gradient-to-br from-indigo-500/15 to-fuchsia-500/10 ring-1 ring-indigo-400/30 p-3.5 shadow-lg shadow-indigo-500/5">
      <div className="flex items-center gap-1.5 mb-2">
        <div className="w-5 h-5 rounded-full bg-gradient-to-br from-indigo-400 to-fuchsia-400 flex items-center justify-center text-[10px]">
          ✨
        </div>
        <div className="text-[11px] uppercase tracking-wider text-indigo-300/90 font-semibold">
          Plans · pinned
        </div>
      </div>

      <div className="text-[14px] leading-snug text-neutral-100">
        Hey — chat expires soon. Y'all are free{" "}
        <b className="text-white">{windowText}</b>.
        <div className="mt-2 rounded-xl bg-black/30 ring-1 ring-white/5 p-2.5">
          <div className="text-[13px] font-semibold text-white">
            {proposal.event.title}
          </div>
          <div className="text-[11px] text-neutral-400 mt-0.5">
            {proposal.event.location} · {eventTime} ·{" "}
            {proposal.event.price === 0 ? "Free" : `$${proposal.event.price}`}
          </div>
        </div>
        <div className="mt-2">Want me to set it up?</div>
      </div>

      {state === "idle" && (
        <div className="mt-3 grid grid-cols-3 gap-2">
          <button
            onClick={onBook}
            className="col-span-2 rounded-full bg-white text-black text-[13px] font-semibold py-2 active:scale-95 transition"
          >
            Book it
          </button>
          <button className="rounded-full bg-white/5 ring-1 ring-white/10 text-[13px] py-2 text-neutral-300">
            Skip
          </button>
        </div>
      )}

      {state === "booking" && (
        <BookingChecklist userNames={userNames} onDone={onChecklistDone} />
      )}

      {state === "booked" && (
        <div className="mt-3 rounded-xl bg-emerald-500/10 ring-1 ring-emerald-400/30 px-3 py-2 text-[13px] text-emerald-200">
          Done. Added to {userNames.length} calendars. Expiry reset — 30 days.
        </div>
      )}
    </div>
  );
}
