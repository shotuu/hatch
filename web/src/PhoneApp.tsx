import { useState } from "react";
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
  const [view, setView] = useState<"list" | "chat">("list");

  if (view === "chat") {
    return (
      <ChatView
        viewer={viewer}
        actions={actions}
        onBack={() => setView("list")}
      />
    );
  }

  return (
    <ChatListView
      viewer={viewer}
      snapshot={actions.snapshot}
      onOpenChat={() => setView("chat")}
    />
  );
}
