import type { User } from "./types";

type Props = {
  author: User;
  text: string;
  ts: string;
  isMe: boolean;
};

export default function MessageBubble({ author, text, ts, isMe }: Props) {
  if (isMe) {
    return (
      <div className="px-3 py-1 flex flex-col items-end">
        <div className="text-[10px] text-neutral-500 mb-0.5 mr-2">{ts}</div>
        <div className="max-w-[75%] rounded-[20px] rounded-br-md bg-blue-500 px-3.5 py-2 text-[15px] leading-snug text-white">
          {text}
        </div>
      </div>
    );
  }

  return (
    <div className="px-3 py-1 flex items-end gap-2">
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-semibold text-black shrink-0"
        style={{ background: author.color }}
      >
        {author.name[0]}
      </div>
      <div className="flex flex-col">
        <div className="text-[10px] text-neutral-500 mb-0.5 ml-2">
          {author.name} · {ts}
        </div>
        <div className="max-w-[260px] rounded-[20px] rounded-bl-md bg-neutral-800 px-3.5 py-2 text-[15px] leading-snug text-neutral-100">
          {text}
        </div>
      </div>
    </div>
  );
}
