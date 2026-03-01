import type { Metadata } from "next";
import { ChatInterface } from "@/components/chat/ChatInterface";

export const metadata: Metadata = {
  title: "Find Your Probate Solicitor",
  description: "Answer a few questions to get personalised quotes from probate solicitors near you.",
};

export default function ChatPage() {
  return <ChatInterface />;
}
