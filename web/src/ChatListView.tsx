import { motion } from "framer-motion";
import HatchLogo from "./HatchLogo";
import { NestEgg } from "./Nest";
import type { GroupSnapshot, User } from "./types";

type Props = {
  viewer: User;
  snapshot: GroupSnapshot;
  onOpenChat: () => void;
};

type DummyChat = {
  id: string;
  name: string;
  preview: string;
  ts: string;
  warmth: number;
  members: { id: string; name: string; color: string }[];
};

const DUMMY_CHATS: DummyChat[] = [
  {
    id: "hoops",
    name: "Hoops Squad 🏀",
    preview: "Marc: run 5s tonight 8pm",
    ts: "11:14 AM",
    warmth: 26,
    members: [
      { id: "marc", name: "Marc", color: "#FF7A45" },
      { id: "tre", name: "Tre", color: "#34D399" },
      { id: "kev", name: "Kev", color: "#B5A3FF" },
    ],
  },
  {
    id: "ramen",
    name: "Ramen Run 🍜",
    preview: "Kenji: line is short rn",
    ts: "Yesterday",
    warmth: 14,
    members: [
      { id: "kenji", name: "Kenji", color: "#FF7A45" },
      { id: "ari", name: "Ari", color: "#34D399" },
      { id: "lin", name: "Lin", color: "#B5A3FF" },
    ],
  },
  {
    id: "bookclub",
    name: "Bookclub 📚",
    preview: "Dani: chapters 6–9 by thurs",
    ts: "Tue",
    warmth: 8,
    members: [
      { id: "dani", name: "Dani", color: "#B5A3FF" },
      { id: "rishi", name: "Rishi", color: "#60A5FA" },
      { id: "fer", name: "Fer", color: "#FF7A45" },
    ],
  },
  {
    id: "trails",
    name: "Trail Squad 🌲",
    preview: "Wes: Solstice loop sat 7am",
    ts: "Sun",
    warmth: 3,
    members: [
      { id: "wes", name: "Wes", color: "#FF9466" },
      { id: "june", name: "June", color: "#FBBF24" },
    ],
  },
];

export default function ChatListView({ snapshot, onOpenChat }: Props) {
  const { messages, current_proposal, expiry_days, users } = snapshot;
  const lastUserMsg = [...messages].reverse().find((m) => m.kind === "user");
  const previewText = current_proposal
    ? `Hatch · ${current_proposal.event.title}`
    : lastUserMsg?.text || "miss y'all 😭";
  const unread = !!current_proposal && current_proposal.status === "pending";

  return (
    <div className="flex flex-col h-full bg-cream-50">
      <header className="px-4 pt-3 pb-3 border-b border-ink-faint/40">
        <div className="flex items-center justify-center gap-2">
          <HatchLogo size={28} />
          <div className="text-[22px] font-semibold tracking-tight text-coral-700 leading-none">
            Hatch
          </div>
        </div>
        <div className="mt-2 flex items-baseline justify-between">
          <div className="text-[16px] font-semibold text-ink leading-tight">
            Messages
          </div>
          <div className="text-[10px] text-ink-subtle">
            {DUMMY_CHATS.length + 1} chats
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto no-scrollbar">
        <ChatRow
          name="LA Friends"
          previewText={previewText}
          ts="now"
          members={users}
          warmth={expiry_days}
          unread={unread}
          onClick={onOpenChat}
        />
        {DUMMY_CHATS.map((c) => (
          <ChatRow
            key={c.id}
            name={c.name}
            previewText={c.preview}
            ts={c.ts}
            members={c.members as User[]}
            warmth={c.warmth}
            onClick={() => {}}
          />
        ))}
      </div>
    </div>
  );
}

type RowProps = {
  name: string;
  previewText: string;
  ts: string;
  members: User[];
  warmth: number;
  unread?: boolean;
  onClick: () => void;
};

function ChatRow({ name, previewText, ts, members, warmth, unread, onClick }: RowProps) {
  return (
    <motion.div
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") onClick();
      }}
      className="w-full px-4 py-3 flex items-start gap-3 border-b border-ink-faint/30 hover:bg-cream-100/60 transition-colors cursor-pointer"
    >
      <div className="flex -space-x-2 shrink-0 mt-0.5">
        {members.slice(0, 3).map((u) => (
          <div
            key={u.id}
            className="w-8 h-8 rounded-full ring-2 ring-cream-50 flex items-center justify-center text-[11px] font-semibold text-white"
            style={{ background: u.color }}
          >
            {u.name[0]}
          </div>
        ))}
      </div>
      <div className="flex-1 min-w-0 text-left">
        <div className="flex items-baseline justify-between gap-2">
          <div className="text-[15px] font-semibold text-ink truncate">{name}</div>
          <div className="text-[11px] text-ink-subtle shrink-0">{ts}</div>
        </div>
        <div className="text-[13px] text-ink-muted truncate mt-0.5">{previewText}</div>
      </div>
      <div className="flex items-center gap-2 mt-0.5">
        {unread && <div className="w-2 h-2 rounded-full bg-coral-500" />}
        <NestEgg warmth={warmth} />
      </div>
    </motion.div>
  );
}
