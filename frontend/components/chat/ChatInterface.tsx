"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, Save } from "lucide-react";
import { toast } from "sonner";
import { sessionsApi } from "@/lib/api";
import { MessageBubble } from "./MessageBubble";
import { OptionChips } from "./OptionChips";
import { PropertyPostcode } from "./PropertyPostcode";
import { TextInput } from "./TextInput";
import { ProgressBar } from "./ProgressBar";
import { IntakeStepper } from "./IntakeStepper";
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
  section?: string;
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
  scorecard_preference?: string;
  include_distance?: boolean;
  is_complete: boolean;
  expires_at: string;
};

type SchemaResponse = {
  practice_area: string;
  questions: Question[];
};

export function ChatInterface() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [session, setSession] = useState<Session | null>(null);
  const [schema, setSchema] = useState<Question[] | null>(null);
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
    let cancelled = false;
    (async () => {
      try {
        const data = (await sessionsApi.schema()) as SchemaResponse;
        if (!cancelled) setSchema(data.questions);
      } catch {
        // Stepper falls back to step-only display if the schema fails to load.
      }
    })();

    const existingSessionId = searchParams.get("session");
    if (existingSessionId) {
      resumeSession(existingSessionId);
    } else {
      startSession();
    }
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function startSession() {
    try {
      const data = await sessionsApi.create("residential_conveyancing");
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
        setTimeout(() => {
          router.push(`/results/${session.session_id}`);
        }, 800);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Something went wrong.";
      toast.error(message);
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
  const stepperQuestions = schema ?? [];

  return (
    <div className="flex h-[calc(100vh-64px)]">
      <IntakeStepper
        questions={stepperQuestions}
        currentQuestionId={session.current_question?.id ?? null}
        answers={session.answers}
      />

      <div className="flex-1 flex flex-col max-w-3xl mx-auto w-full">
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
              <PropertyPostcode
                placeholder={session.current_question.placeholder}
                hint={session.current_question.hint}
                onSubmit={(value) => handleAnswer(value)}
                disabled={submitting}
              />
            )}
            {(session.current_question.type === "currency" ||
              session.current_question.type === "text" ||
              session.current_question.type === "email" ||
              session.current_question.type === "tel") && (
              <TextInput
                type={session.current_question.type}
                placeholder={session.current_question.placeholder}
                hint={session.current_question.hint}
                onSubmit={(value) => handleAnswer(value)}
                disabled={submitting}
              />
            )}
          </div>
        )}
      </div>

      {saveModalOpen && session && (
        <SaveModal
          sessionId={session.session_id}
          onClose={() => setSaveModalOpen(false)}
        />
      )}
    </div>
  );
}
