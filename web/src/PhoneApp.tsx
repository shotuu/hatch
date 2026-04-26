import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import ChatListView from "./ChatListView";
import ChatView from "./ChatView";
import type { GroupActions } from "./state";
import type { User } from "./types";

type Props = {
  viewer: User;
  actions: GroupActions;
};

/** Per-phone shell. Each phone holds its own list-vs-chat state so multiple
 * phones in the demo can be on different screens simultaneously. */
export default function PhoneApp({ viewer, actions }: Props) {
  const [view, setView] = useState<"chats" | "chat">("chat");
  const messageCount = actions.snapshot.messages.length;
  const [lastReadCount, setLastReadCount] = useState(messageCount);
  const unreadCount =
    view === "chat" ? 0 : Math.max(0, messageCount - lastReadCount);

  useEffect(() => {
    if (view === "chat") setLastReadCount(messageCount);
  }, [messageCount, view]);

  const openChat = () => {
    setLastReadCount(messageCount);
    setView("chat");
  };

  return (
    <div className="relative w-full h-full overflow-hidden">
      <ChatListView
        viewer={viewer}
        snapshot={actions.snapshot}
        unreadCount={unreadCount}
        onOpenChat={openChat}
      />

      <AnimatePresence initial={false}>
        {view === "chat" && (
          <motion.div
            key="chat"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%", pointerEvents: "none" }}
            transition={{ type: "spring", stiffness: 320, damping: 34 }}
            className="absolute inset-0 bg-cream-50"
          >
            <ChatView
              viewer={viewer}
              actions={actions}
              onBack={() => setView("chats")}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
