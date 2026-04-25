import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import ChatListView from "./ChatListView";
import ChatView from "./ChatView";
import type { GroupActions } from "./state";
import type { User } from "./types";

type Props = {
  viewer: User;
  actions: GroupActions;
};

export default function PhoneApp({ viewer, actions }: Props) {
  const [view, setView] = useState<"chats" | "chat">("chat");

  return (
    <div className="relative w-full h-full overflow-hidden">
      <ChatListView
        viewer={viewer}
        snapshot={actions.snapshot}
        onOpenChat={() => setView("chat")}
      />

      <AnimatePresence initial={false}>
        {view === "chat" && (
          <motion.div
            key="chat"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
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
