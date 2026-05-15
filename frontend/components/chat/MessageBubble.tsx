"use client";

import { cn } from "@/lib/utils";

type Message = {
  role: "system" | "user";
  content: string;
  question_id?: string;
  timestamp: string;
};

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-5 py-3 text-sm leading-relaxed text-navy animate-fade-in",
          isUser ? "bg-teal" : "bg-mint",
        )}
      >
        {message.content}
      </div>
    </div>
  );
}
