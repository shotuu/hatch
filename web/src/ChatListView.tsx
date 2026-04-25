import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import HatchLogo from "./HatchLogo";
import { NestEgg } from "./Nest";
import type { GroupSnapshot, User } from "./types";

type Props = {
  viewer: User;
  snapshot: GroupSnapshot;
  unreadCount: number;
  onOpenChat: () => void;
};

type DummyChat = {
  id: string;
  name: string;
  preview: string;
  ts: string;
  expiryDays: number;
  members: { id: string; name: string; color: string }[];
};

const DUMMY_CHATS_BY_USER: Record<string, DummyChat[]> = {
  daniel: [
    {
      id: "art-crit",
      name: "Art Crit Group 🎨",
      preview: "Mira: studio open at 4?",
      ts: "10:48 AM",
      expiryDays: 18,
      members: [
        { id: "mira", name: "Mira", color: "#B5A3FF" },
        { id: "owen", name: "Owen", color: "#FF9466" },
        { id: "yuna", name: "Yuna", color: "#5BC586" },
      ],
    },
    {
      id: "coffee-hunters",
      name: "Coffee Hunters ☕",
      preview: "Theo: that pourover at Maru 🤌",
      ts: "9:02 AM",
      expiryDays: 4,
      members: [
        { id: "theo", name: "Theo", color: "#FFC857" },
        { id: "ines", name: "Ines", color: "#F472B6" },
        { id: "rohan", name: "Rohan", color: "#60A5FA" },
      ],
    },
    {
      id: "ramen-run",
      name: "Ramen Run 🍜",
      preview: "Kenji: line is short rn",
      ts: "Yesterday",
      expiryDays: 12,
      members: [
        { id: "kenji", name: "Kenji", color: "#FF7A45" },
        { id: "ari", name: "Ari", color: "#34D399" },
        { id: "lin", name: "Lin", color: "#B5A3FF" },
        { id: "noa", name: "Noa", color: "#FBBF24" },
      ],
    },
    {
      id: "fam-d",
      name: "Family ❤️",
      preview: "Mom: did you eat?",
      ts: "Mon",
      expiryDays: 25,
      members: [
        { id: "mom-d", name: "Mom", color: "#F472B6" },
        { id: "dad-d", name: "Dad", color: "#60A5FA" },
        { id: "sis-d", name: "Liv", color: "#FBBF24" },
      ],
    },
  ],
  jono: [
    {
      id: "hoops",
      name: "Hoops Squad 🏀",
      preview: "Marc: run 5s tonight 8pm",
      ts: "11:14 AM",
      expiryDays: 21,
      members: [
        { id: "marc", name: "Marc", color: "#FF7A45" },
        { id: "tre", name: "Tre", color: "#34D399" },
        { id: "deion", name: "Dee", color: "#60A5FA" },
        { id: "kev", name: "Kev", color: "#B5A3FF" },
      ],
    },
    {
      id: "comedy",
      name: "Open Mic Crew",
      preview: "Sasha: i bombed it 💀",
      ts: "10:01 AM",
      expiryDays: 9,
      members: [
        { id: "sasha", name: "Sasha", color: "#F472B6" },
        { id: "leo-c", name: "Leo", color: "#FFC857" },
        { id: "rae", name: "Rae", color: "#5BC586" },
      ],
    },
    {
      id: "barcrawl",
      name: "Bar Crawl 🍻",
      preview: "Mateo: sunset on the rooftop?",
      ts: "Yesterday",
      expiryDays: 3,
      members: [
        { id: "mateo", name: "Mateo", color: "#FF9466" },
        { id: "kira", name: "Kira", color: "#B5A3FF" },
        { id: "hank", name: "Hank", color: "#60A5FA" },
        { id: "zane", name: "Zane", color: "#34D399" },
        { id: "max", name: "Max", color: "#FFC857" },
      ],
    },
    {
      id: "bbq",
      name: "BBQ Sundays",
      preview: "Cole: ribs are on at 3",
      ts: "Sun",
      expiryDays: 14,
      members: [
        { id: "cole", name: "Cole", color: "#FF7A45" },
        { id: "ren-b", name: "Ren", color: "#5BC586" },
        { id: "tash", name: "Tash", color: "#F472B6" },
      ],
    },
  ],
  andrew: [
    {
      id: "yoga",
      name: "Sunrise Yoga 🧘",
      preview: "Priya: 6:30 at the pier ✨",
      ts: "8:42 AM",
      expiryDays: 27,
      members: [
        { id: "priya-y", name: "Priya", color: "#5BC586" },
        { id: "elle", name: "Elle", color: "#B5A3FF" },
        { id: "ben", name: "Ben", color: "#FFC857" },
      ],
    },
    {
      id: "veggie",
      name: "Veggie Roomies 🥬",
      preview: "Sage: I'm making pad see ew",
      ts: "12:30 PM",
      expiryDays: 11,
      members: [
        { id: "sage", name: "Sage", color: "#34D399" },
        { id: "ivy", name: "Ivy", color: "#F472B6" },
        { id: "kai-v", name: "Kai", color: "#60A5FA" },
      ],
    },
    {
      id: "trails",
      name: "Trail Squad 🌲",
      preview: "Wes: Solstice loop sat 7am",
      ts: "Yesterday",
      expiryDays: 5,
      members: [
        { id: "wes", name: "Wes", color: "#FF9466" },
        { id: "june", name: "June", color: "#FBBF24" },
        { id: "tomo", name: "Tomo", color: "#B5A3FF" },
        { id: "ash", name: "Ash", color: "#5BC586" },
      ],
    },
    {
      id: "bookclub",
      name: "Bookclub 📚",
      preview: "Dani: chapters 6–9 by thurs",
      ts: "Tue",
      expiryDays: 16,
      members: [
        { id: "dani", name: "Dani", color: "#B5A3FF" },
        { id: "rishi", name: "Rishi", color: "#60A5FA" },
        { id: "fer", name: "Fer", color: "#FF7A45" },
      ],
    },
  ],
};

const FALLBACK_DUMMY_CHATS: DummyChat[] = DUMMY_CHATS_BY_USER.daniel;

const ARCHIVED_CHATS: DummyChat[] = [
  {
    id: "museum-loop",
    name: "Museum Loop",
    preview: "Archived cold · no plan hatched",
    ts: "Mar 18",
    expiryDays: 0,
    members: [
      { id: "mara", name: "Mara", color: "#B5A3FF" },
      { id: "eli", name: "Eli", color: "#FF9466" },
      { id: "nina", name: "Nina", color: "#5BC586" },
    ],
  },
  {
    id: "beach-day",
    name: "Beach Day",
    preview: "Archived cold · thread went quiet",
    ts: "Feb 02",
    expiryDays: 0,
    members: [
      { id: "sam-b", name: "Sam", color: "#FFC857" },
      { id: "jo", name: "Jo", color: "#60A5FA" },
      { id: "liv-b", name: "Liv", color: "#F472B6" },
    ],
  },
];

export default function ChatListView({
  viewer,
  snapshot,
  unreadCount,
  onOpenChat,
}: Props) {
  const { messages, current_proposal, nest_warmth, users } = snapshot;
  const [folder, setFolder] = useState<"active" | "archive">("active");
  const lastUserMsg = [...messages].reverse().find((m) => m.kind === "user");
  const lastAuthor = lastUserMsg?.author_id
    ? users.find((u) => u.id === lastUserMsg.author_id)
    : undefined;
  const lastAuthorLabel =
    lastAuthor && lastUserMsg
      ? lastAuthor.id === viewer.id
        ? "You"
        : lastAuthor.name
      : null;
  const previewText = current_proposal
    ? `Hatch · ${current_proposal.event.title}`
    : lastUserMsg
    ? `${lastAuthorLabel ? lastAuthorLabel + ": " : ""}${lastUserMsg.text || ""}`
    : "miss y'all 😭";
  const newPlan =
    !!current_proposal && current_proposal.status === "pending";
  const dummyChats = DUMMY_CHATS_BY_USER[viewer.id] || FALLBACK_DUMMY_CHATS;
  const mainArchived = nest_warmth <= 0;
  const archivedChats = ARCHIVED_CHATS;
  const totalChats = dummyChats.length + (mainArchived ? 0 : 1);
  const archiveCount = archivedChats.length + (mainArchived ? 1 : 0);
  const showingArchive = folder === "archive";

  return (
    <div className="flex flex-col h-full bg-cream-50">
      <header className="px-4 pt-3 pb-3 border-b border-ink-faint/40">
        <div className="flex items-center justify-center gap-2">
          <HatchLogo size={30} />
          <div className="text-[24px] font-semibold tracking-tight text-coral-700 leading-none">
            Hatch
          </div>
        </div>
        <div className="mt-2 flex items-baseline justify-between">
          <div className="text-[17px] font-semibold text-ink leading-tight">
            {showingArchive ? "Archive" : "Messages"}
          </div>
          <div className="flex items-center gap-2">
            <motion.button
              whileTap={{ scale: 0.94 }}
              onClick={() => setFolder((v) => (v === "active" ? "archive" : "active"))}
              className={`rounded-full px-2.5 py-1 text-[10.5px] font-semibold ring-1 transition-colors ${
                showingArchive
                  ? "bg-coral-500 text-white ring-coral-500"
                  : "bg-white text-coral-700 ring-coral-200"
              }`}
              aria-pressed={showingArchive}
            >
              {showingArchive ? "Messages" : `Archive ${archiveCount}`}
            </motion.button>
            <div className="text-[10px] text-ink-subtle">
              {showingArchive ? archiveCount : totalChats} chats
            </div>
          </div>
        </div>
      </header>

      {!showingArchive && unreadCount > 0 && (
        <motion.button
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          whileTap={{ scale: 0.98 }}
          onClick={onOpenChat}
          className="mx-4 mt-3 rounded-2xl bg-coral-500 text-white px-3 py-2 text-left shadow-warm flex items-center justify-between"
        >
          <span className="text-[12.5px] font-semibold">
            {unreadCount} unread in LA Friends
          </span>
          <span className="text-[11px] opacity-90">Open</span>
        </motion.button>
      )}

      <div className="flex-1 overflow-y-auto no-scrollbar">
        {showingArchive ? (
          <>
            {mainArchived && (
              <ChatRow
                name="LA Friends"
                previewText="Archived cold · countdown hit zero"
                ts="now"
                avatarCluster={users}
                expiryDays={nest_warmth}
                archived
                onClick={onOpenChat}
              />
            )}
            {archivedChats.map((c) => (
              <ChatRow
                key={c.id}
                name={c.name}
                previewText={c.preview}
                ts={c.ts}
                avatarCluster={c.members as User[]}
                expiryDays={c.expiryDays}
                archived
                onClick={() => {}}
              />
            ))}
          </>
        ) : (
          <>
            {!mainArchived && (
              <ChatRow
                name="LA Friends"
                previewText={previewText}
                ts="now"
                avatarCluster={users}
                expiryDays={nest_warmth}
                unread={unreadCount > 0}
                unreadCount={unreadCount}
                newPlan={newPlan}
                onClick={onOpenChat}
              />
            )}
            {dummyChats.map((c) => (
              <ChatRow
                key={c.id}
                name={c.name}
                previewText={c.preview}
                ts={c.ts}
                avatarCluster={c.members as User[]}
                expiryDays={c.expiryDays}
                onClick={() => {}}
              />
            ))}
          </>
        )}
      </div>
    </div>
  );
}

type RowProps = {
  name: string;
  previewText: string;
  ts: string;
  avatarCluster: User[];
  expiryDays: number;
  unread?: boolean;
  unreadCount?: number;
  newPlan?: boolean;
  archived?: boolean;
  onClick: () => void;
};

function ChatRow({
  name,
  previewText,
  ts,
  avatarCluster,
  expiryDays,
  unread,
  unreadCount = 0,
  newPlan,
  archived,
  onClick,
}: RowProps) {
  const [membersOpen, setMembersOpen] = useState(false);
  const visible = avatarCluster.slice(0, 3);
  const overflowCount = Math.max(0, avatarCluster.length - 3);
  const hasOverflow = overflowCount > 0;

  return (
    <div className="border-b border-ink-faint/30">
      <motion.div
        whileTap={{ scale: 0.98 }}
        onClick={onClick}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") onClick();
        }}
        className="w-full px-4 py-3 flex items-start gap-3 hover:bg-cream-100/60 transition-colors cursor-pointer focus:outline-none focus-visible:bg-cream-100"
      >
        <div className="flex -space-x-2 shrink-0 mt-0.5">
          {visible.map((u) => (
            <div
              key={u.id}
              className="w-8 h-8 rounded-full ring-2 ring-cream-50 flex items-center justify-center text-[11px] font-semibold text-white"
              style={{ background: u.color }}
            >
              {u.name[0]}
            </div>
          ))}
          {hasOverflow && (
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={(e) => {
                e.stopPropagation();
                setMembersOpen((v) => !v);
              }}
              aria-expanded={membersOpen}
              aria-label={
                membersOpen
                  ? "Hide all members"
                  : `Show all ${avatarCluster.length} members`
              }
              className="w-8 h-8 rounded-full ring-2 ring-cream-50 bg-cream-200 flex items-center justify-center text-[10px] font-semibold text-ink-muted hover:bg-cream-300 hover:text-ink transition-colors"
            >
              +{overflowCount}
            </motion.button>
          )}
        </div>
        <div className="flex-1 min-w-0 text-left">
          <div className="flex items-baseline justify-between gap-2">
            <div className="text-[15px] font-semibold text-ink truncate">{name}</div>
            <div className="text-[11px] text-ink-subtle shrink-0">{ts}</div>
          </div>
          <div className="text-[13px] text-ink-muted truncate mt-0.5">{previewText}</div>
        </div>
        <div className="flex items-center gap-2 mt-0.5 shrink-0">
          {archived && (
            <span className="px-1.5 py-0.5 rounded-full bg-cream-200 text-[9px] font-semibold uppercase tracking-wide text-ink-muted">
              old
            </span>
          )}
          {newPlan && (
            <motion.div
              animate={{ scale: [1, 1.06, 1] }}
              transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
              className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-gradient-to-r from-coral-500 to-yolk text-white text-[9px] font-bold uppercase tracking-wide ring-2 ring-cream-50 shadow-warm"
              title="New plan suggested"
            >
              <span aria-hidden>🥚</span>
              <span>plan</span>
            </motion.div>
          )}
          {unread && (
            <div className="min-w-5 h-5 px-1.5 rounded-full bg-coral-500 text-white text-[10px] font-bold flex items-center justify-center ring-2 ring-cream-50">
              {unreadCount}
            </div>
          )}
          <NestEgg warmth={expiryDays} />
        </div>
      </motion.div>

      <AnimatePresence initial={false}>
        {membersOpen && (
          <motion.div
            key="members"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-3 pt-0.5 flex flex-wrap gap-1.5">
              {avatarCluster.map((u) => (
                <div
                  key={u.id}
                  className="flex items-center gap-1.5 rounded-full bg-white ring-1 ring-ink-faint/40 pl-0.5 pr-3 py-0.5 shadow-bubble"
                >
                  <div
                    className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-semibold text-white"
                    style={{ background: u.color }}
                  >
                    {u.name[0]}
                  </div>
                  <span className="text-[11.5px] text-ink leading-none">{u.name}</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
