import DemoPanel from "./DemoPanel";
import PhoneApp from "./PhoneApp";
import PhoneFrame from "./PhoneFrame";
import { useGroupState } from "./state";

export default function App() {
  const actions = useGroupState();
  const { users } = actions.snapshot;

  return (
    <div className="min-h-screen bg-gradient-to-br from-cream-100 via-cream-50 to-coral-50 cream-grain">
      <div className="min-h-screen flex flex-col xl:flex-row items-center xl:items-start justify-center gap-6 p-6 xl:p-10 overflow-x-auto">
        {users.length > 0 ? (
          <div className="flex flex-col xl:flex-row gap-6 items-center xl:items-start">
            {users.map((u) => (
              <PhoneFrame key={u.id} label={u.name}>
                <PhoneApp viewer={u} actions={actions} />
              </PhoneFrame>
            ))}
          </div>
        ) : (
          <PhoneFrame>
            <div className="flex items-center justify-center h-full text-ink-subtle text-[13px]">
              Loading…
            </div>
          </PhoneFrame>
        )}

        <DemoPanel actions={actions} />
      </div>
    </div>
  );
}
