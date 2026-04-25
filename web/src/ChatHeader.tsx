import type { User } from "./types";

type Props = {
  tripName: string;
  members: User[];
  expiryDays: number;
};

export default function ChatHeader({ tripName, members, expiryDays }: Props) {
  const expiryColor =
    expiryDays <= 7
      ? "bg-rose-500/20 text-rose-200 ring-rose-400/40"
      : expiryDays <= 14
      ? "bg-amber-500/20 text-amber-200 ring-amber-400/40"
      : "bg-emerald-500/20 text-emerald-200 ring-emerald-400/40";

  return (
    <header className="px-4 py-3 border-b border-white/10 bg-neutral-950/95 backdrop-blur sticky top-0 z-10">
      <div className="flex items-center justify-between">
        <button className="text-indigo-400 text-[15px] font-medium">‹</button>

        <div className="flex flex-col items-center">
          <div className="flex -space-x-2 mb-1">
            {members.map((m) => (
              <div
                key={m.id}
                className="w-7 h-7 rounded-full ring-2 ring-neutral-950 flex items-center justify-center text-[11px] font-semibold text-black"
                style={{ background: m.color }}
              >
                {m.name[0]}
              </div>
            ))}
          </div>
          <div className="text-[13px] font-semibold text-white">
            {tripName}
          </div>
          <div className="text-[10px] text-neutral-500">
            {members.map((m) => m.name).join(" · ")}
          </div>
        </div>

        <div
          className={`text-[10px] font-semibold px-2 py-1 rounded-full ring-1 ${expiryColor}`}
        >
          {expiryDays}d left
        </div>
      </div>
    </header>
  );
}
