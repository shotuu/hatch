import { ReactNode } from "react";

export default function PhoneFrame({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="relative w-[390px] h-[844px] rounded-[44px] bg-black shadow-2xl ring-1 ring-white/10 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-36 h-7 bg-black rounded-b-2xl z-20" />
        <div className="h-full w-full bg-neutral-950 pt-8">{children}</div>
      </div>
    </div>
  );
}
