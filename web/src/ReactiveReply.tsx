import { useState } from "react";
import type { Event } from "./types";

type Props = {
  query: string;
  matches: Event[];
};

export default function ReactiveReply({ query, matches }: Props) {
  const [open, setOpen] = useState(false);

  if (matches.length === 0) return null;

  return (
    <div className="px-3 py-1 flex items-end gap-2">
      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-400 to-fuchsia-400 flex items-center justify-center text-[11px] shrink-0">
        ✨
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[10px] text-indigo-300 mb-0.5 ml-2">
          Plans · just now
        </div>
        <button
          onClick={() => setOpen(!open)}
          className="w-full text-left rounded-2xl rounded-bl-md bg-neutral-800/80 ring-1 ring-indigo-400/20 px-3.5 py-2 text-[14px] text-neutral-100"
        >
          <div className="flex items-center justify-between gap-2">
            <span>
              Found <b>{matches.length}</b> option{matches.length === 1 ? "" : "s"}{" "}
              for <span className="text-indigo-300">"{query}"</span>
            </span>
            <span
              className={`text-[11px] text-neutral-400 transition-transform ${
                open ? "rotate-180" : ""
              }`}
            >
              ▾
            </span>
          </div>

          {open && (
            <div className="mt-2 space-y-2">
              {matches.slice(0, 3).map((e) => (
                <div
                  key={e.id}
                  className="rounded-xl bg-black/30 ring-1 ring-white/5 p-2.5"
                >
                  <div className="text-[13px] font-semibold text-white">
                    {e.title}
                  </div>
                  <div className="text-[11px] text-neutral-400 mt-0.5">
                    {e.location} ·{" "}
                    {new Date(e.datetime).toLocaleDateString(undefined, {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                    })}{" "}
                    · {e.price === 0 ? "Free" : `$${e.price}`}
                  </div>
                  <div className="mt-2 flex gap-1.5">
                    <span className="flex-1 text-center rounded-full bg-white/10 text-[11px] py-1 text-neutral-200">
                      Propose to group
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </button>
      </div>
    </div>
  );
}
