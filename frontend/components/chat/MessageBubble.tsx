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
          "max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed animate-fade-in",
          isUser
            ? "bg-brand-600 text-white rounded-br-sm"
            : "bg-white border border-gray-200 text-gray-800 rounded-bl-sm shadow-sm",
        )}
      >
        {message.content}
      </div>
    </div>
  );
}
