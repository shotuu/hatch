import { ReactNode } from "react";

export default function PhoneFrame({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gradient-to-br from-cream-100 via-cream-50 to-coral-50 cream-grain">
      <div className="relative w-[390px] h-[844px] rounded-[48px] bg-cream-50 shadow-warmlg ring-1 ring-ink-faint/40 overflow-hidden">
        {/* Dynamic Island */}
        <div className="absolute top-2.5 left-1/2 -translate-x-1/2 w-32 h-7 bg-ink rounded-full z-30" />

        {/* iOS status bar */}
        <div className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between px-8 pt-3.5 text-[13px] font-semibold text-ink pointer-events-none">
          <span>9:41</span>
          <div className="flex items-center gap-1.5">
            <SignalIcon />
            <WifiIcon />
            <BatteryIcon />
          </div>
        </div>

        <div className="h-full w-full bg-cream-50 pt-12 flex flex-col">
          {children}
        </div>
      </div>
    </div>
  );
}

function SignalIcon() {
  return (
    <svg width="17" height="11" viewBox="0 0 17 11" fill="currentColor">
      <rect x="0" y="7" width="3" height="4" rx="1" />
      <rect x="4.5" y="5" width="3" height="6" rx="1" />
      <rect x="9" y="3" width="3" height="8" rx="1" />
      <rect x="13.5" y="0" width="3" height="11" rx="1" />
    </svg>
  );
}

function WifiIcon() {
  return (
    <svg width="15" height="11" viewBox="0 0 15 11" fill="currentColor">
      <path d="M7.5 1C4.6 1 1.9 2 0 3.6l1.5 1.5C3 3.8 5.2 3 7.5 3s4.5.8 6 2.1L15 3.6C13.1 2 10.4 1 7.5 1zm0 4C5.6 5 3.9 5.7 2.6 6.9L4.1 8.4c.9-.9 2.1-1.4 3.4-1.4s2.5.5 3.4 1.4l1.5-1.5C11.1 5.7 9.4 5 7.5 5zm0 4c-.8 0-1.6.3-2.1.9L7.5 11l2.1-2.1c-.5-.6-1.3-.9-2.1-.9z" />
    </svg>
  );
}

function BatteryIcon() {
  return (
    <svg width="27" height="13" viewBox="0 0 27 13" fill="none">
      <rect
        x="0.5"
        y="0.5"
        width="22"
        height="12"
        rx="3"
        stroke="currentColor"
        strokeOpacity="0.4"
      />
      <rect x="2" y="2" width="19" height="9" rx="1.5" fill="currentColor" />
      <rect
        x="24"
        y="4"
        width="2"
        height="5"
        rx="1"
        fill="currentColor"
        fillOpacity="0.4"
      />
    </svg>
  );
}
