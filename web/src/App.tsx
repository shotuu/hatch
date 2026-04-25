import ChatView from "./ChatView";
import DemoPanel from "./DemoPanel";
import PhoneFrame from "./PhoneFrame";
import { useHatchState } from "./state";

export default function App() {
  const state = useHatchState();

  return (
    <div className="min-h-screen bg-gradient-to-br from-cream-100 via-cream-50 to-coral-50 cream-grain">
      <div className="min-h-screen flex flex-col lg:flex-row items-center lg:items-start justify-center gap-8 p-6 lg:p-10">
        <PhoneFrame>
          <ChatView
            expiryDays={state.expiryDays}
            messages={state.messages}
            proposal={state.proposal}
            busy={state.busy}
            scrollRef={state.scrollRef}
            onBooked={state.onBooked}
          />
        </PhoneFrame>

        <DemoPanel
          busy={state.busy}
          wipeStatus={state.wipeStatus}
          triggerProactive={state.triggerProactive}
          triggerReactive={state.triggerReactive}
          reset={state.reset}
          onWipe={state.onWipe}
        />
      </div>
    </div>
  );
}
