"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, Save } from "lucide-react";
import { toast } from "sonner";
import { sessionsApi } from "@/lib/api";
import { MessageBubble } from "./MessageBubble";
import { OptionChips } from "./OptionChips";
import { PostcodeInput } from "./PostcodeInput";
import { ProgressBar } from "./ProgressBar";
import { AnswerSidebar } from "./AnswerSidebar";
import { SaveModal } from "./SaveModal";

const TOTAL_STEPS = 13;

type Message = {
  role: "system" | "user";
  content: string;
  question_id?: string;
  timestamp: string;
};

type Question = {
  id: string;
  step: number;
  text: string;
  type: string;
  options?: { value: string; label: string; description?: string }[];
  placeholder?: string;
  hint?: string;
};

type Session = {
  session_id: string;
  practice_area: string;
  current_question: Question | null;
  message_history: Message[];
  answers: Record<string, string | string[]>;
  is_complete: boolean;
  expires_at: string;
};

export function ChatInterface() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [saveModalOpen, setSaveModalOpen] = useState(false);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [session?.message_history, scrollToBottom]);

  useEffect(() => {
    const existingSessionId = searchParams.get("session");
    if (existingSessionId) {
      resumeSession(existingSessionId);
    } else {
      startSession();
    }
  }, []);

  async function startSession() {
    try {
      const data = await sessionsApi.create("probate");
      setSession(data as Session);
    } catch {
      toast.error("Failed to start session. Please refresh and try again.");
    } finally {
      setLoading(false);
    }
  }

  async function resumeSession(sessionId: string) {
    try {
      const data = await sessionsApi.get(sessionId);
      setSession(data as Session);
      if ((data as Session).is_complete) {
        router.push(`/results/${sessionId}`);
      }
    } catch {
      // Session not found or expired — start fresh
      await startSession();
    } finally {
      setLoading(false);
    }
  }

  async function handleAnswer(answer: string | string[]) {
    if (!session?.current_question || submitting) return;

    setSubmitting(true);
    try {
      const data = await sessionsApi.answer(
        session.session_id,
        session.current_question.id,
        answer as string,
      );
      const updated = data as Session;
      setSession(updated);

      if (updated.is_complete) {
        // Small delay for UX, then navigate to results
        setTimeout(() => {
          router.push(`/results/${session.session_id}`);
        }, 800);
      }
    } catch {
      toast.error("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-64px)]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-brand-600 animate-spin mx-auto mb-3" />
          <p className="text-gray-500">Setting up your comparison...</p>
        </div>
      </div>
    );
  }

  if (!session) return null;

  const currentStep = session.current_question?.step ?? TOTAL_STEPS;
  const progress = session.is_complete ? 100 : ((currentStep - 1) / TOTAL_STEPS) * 100;

  return (
    <div className="flex h-[calc(100vh-64px)]">
      {/* Sidebar — answered questions summary */}
      <AnswerSidebar answers={session.answers} />

      {/* Main chat area */}
      <div className="flex-1 flex flex-col max-w-3xl mx-auto w-full">
        {/* Progress */}
        <div className="px-4 pt-4 pb-2">
          <div className="flex items-center justify-between text-sm text-gray-500 mb-2">
            <span>
              {session.is_complete
                ? "All done!"
                : `Question ${currentStep} of ${TOTAL_STEPS}`}
            </span>
            <button
              onClick={() => setSaveModalOpen(true)}
              className="btn-ghost text-xs gap-1"
              type="button"
            >
              <Save className="w-3.5 h-3.5" /> Save for later
            </button>
          </div>
          <ProgressBar value={progress} />
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {session.message_history.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} />
          ))}

          {submitting && (
            <div className="flex items-center gap-2 text-gray-400 text-sm pl-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Processing...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        {!session.is_complete && session.current_question && (
          <div className="border-t border-gray-200 bg-white px-4 py-4">
            {session.current_question.type === "single_choice" && (
              <OptionChips
                options={session.current_question.options ?? []}
                onSelect={(value) => handleAnswer(value)}
                disabled={submitting}
              />
            )}
            {session.current_question.type === "postcode" && (
              <PostcodeInput
                placeholder={session.current_question.placeholder}
                onSubmit={(value) => handleAnswer(value)}
                disabled={submitting}
              />
            )}
          </div>
        )}
      </div>

      {/* Save modal */}
      {saveModalOpen && session && (
        <SaveModal
          sessionId={session.session_id}
          onClose={() => setSaveModalOpen(false)}
        />
      )}
    </div>
  );
}
