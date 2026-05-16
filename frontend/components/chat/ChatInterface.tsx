"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, ArrowUpRight, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { sessionsApi, type AnswerValue } from "@/lib/api";
import { trackIntakeStarted, trackIntakeCompleted } from "@/lib/analytics";
import { MessageBubble } from "./MessageBubble";
import { OptionChips } from "./OptionChips";
import { TenureWithUnsure } from "./TenureWithUnsure";
import { CheckboxGroup } from "./CheckboxGroup";
import { DualPropertyBlock } from "./DualPropertyBlock";
import { OptionalPostcode } from "./OptionalPostcode";
import { TextInput } from "./TextInput";
import { ChatSidebar } from "./ChatSidebar";
import { SaveModal } from "./SaveModal";

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
  pathways?: string[];
  options?: { value: string; label: string; description?: string }[];
  tenure_options?: { value: string; label: string }[];
  placeholder?: string;
  hint?: string;
};

type Session = {
  session_id: string;
  practice_area: string;
  pathway: string | null;
  current_question: Question | null;
  message_history: Message[];
  answers: Record<string, unknown>;
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
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);

  const isReviseMode = searchParams.get("revise") === "1";

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
        // Sidebar falls back to "answers will appear here" if the schema fails to load.
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
      const created = data as Session;
      setSession(created);
      trackIntakeStarted(created.session_id);
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
      if ((data as Session).is_complete && !isReviseMode) {
        router.push(`/results/${sessionId}`);
      }
    } catch {
      await startSession();
    } finally {
      setLoading(false);
    }
  }

  async function handleAnswer(answer: AnswerValue) {
    if (submitting) return;

    if (editingQuestion) {
      setSubmitting(true);
      try {
        const data = await sessionsApi.updateAnswer(
          session!.session_id,
          editingQuestion.id,
          answer,
        );
        setSession(data as Session);
        setEditingQuestion(null);
        toast.success("Answer updated");
      } catch (err) {
        const message = err instanceof Error ? err.message : "Something went wrong.";
        toast.error(message);
      } finally {
        setSubmitting(false);
      }
      return;
    }

    if (!session?.current_question) return;

    const submittedQuestionId = session.current_question.id;
    setSubmitting(true);
    try {
      const data = await sessionsApi.answer(
        session.session_id,
        submittedQuestionId,
        answer,
      );
      const updated = data as Session;
      setSession(updated);

      if (updated.is_complete) {
        trackIntakeCompleted(session.session_id);
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
          <Loader2 className="w-8 h-8 text-purple animate-spin mx-auto mb-3" />
          <p className="text-ink-muted">Setting up your comparison...</p>
        </div>
      </div>
    );
  }

  if (!session) return null;

  const activeQuestion = editingQuestion ?? session.current_question;
  const showInput = activeQuestion && (!session.is_complete || editingQuestion);

  return (
    <div className="flex h-[calc(100vh-64px)]">
      <ChatSidebar
        questions={schema ?? []}
        answers={session.answers}
        pathway={session.pathway}
        currentStep={session.current_question?.step ?? 5}
        isComplete={session.is_complete}
      />

      <div className="flex-1 flex flex-col max-w-3xl mx-auto w-full">
        {(isReviseMode || session.is_complete || editingQuestion) && (
          <div className="px-4 pt-4 pb-2 flex items-center justify-between text-sm">
            <span className="text-ink-muted">
              {editingQuestion
                ? `Editing: ${editingQuestion.text}`
                : session.is_complete
                  ? "All done!"
                  : ""}
            </span>
            {(isReviseMode || session.is_complete) && (
              <button
                onClick={() => router.push(`/results/${session.session_id}`)}
                className="btn-ghost text-xs gap-1"
                type="button"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back to results
              </button>
            )}
          </div>
        )}

        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {session.message_history.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} />
          ))}

          {editingQuestion && (
            <div className="rounded-lg border border-purple/30 bg-purple/5 px-4 py-3 text-sm text-navy">
              <p className="font-medium">{editingQuestion.text}</p>
              {editingQuestion.hint && (
                <p className="text-xs text-ink-muted mt-1">{editingQuestion.hint}</p>
              )}
              <button
                onClick={() => setEditingQuestion(null)}
                className="text-xs text-purple underline mt-1"
                type="button"
              >
                Cancel edit
              </button>
            </div>
          )}

          {showInput && activeQuestion && (
            <div className="pt-1">
              <QuestionInput
                question={activeQuestion}
                onAnswer={handleAnswer}
                disabled={submitting}
              />
            </div>
          )}

          {submitting && (
            <div className="flex items-center gap-2 text-ink-muted text-sm pl-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Processing...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-gray-200 bg-white px-4 py-3 flex items-center justify-end gap-5 text-sm">
          <button
            onClick={() => {
              if (
                typeof window !== "undefined" &&
                window.confirm("Start a fresh chat? Your current answers will be lost.")
              ) {
                router.push("/chat");
                router.refresh();
              }
            }}
            className="inline-flex items-center gap-1.5 text-navy hover:text-purple transition-colors"
            type="button"
          >
            <ArrowUpRight className="w-3.5 h-3.5 text-purple" />
            Start new chat
          </button>
          <button
            onClick={() => setSaveModalOpen(true)}
            className="inline-flex items-center gap-1.5 text-navy hover:text-purple transition-colors"
            type="button"
          >
            <ArrowUpRight className="w-3.5 h-3.5 text-purple" />
            Save for later
          </button>
        </div>
      </div>

      {saveModalOpen && session && (
        <SaveModal sessionId={session.session_id} onClose={() => setSaveModalOpen(false)} />
      )}
    </div>
  );
}


function QuestionInput({
  question,
  onAnswer,
  disabled,
}: {
  question: Question;
  onAnswer: (a: AnswerValue) => void;
  disabled?: boolean;
}) {
  switch (question.type) {
    case "single_choice":
      return (
        <OptionChips
          options={question.options ?? []}
          onSelect={(value) => onAnswer(value)}
          disabled={disabled}
        />
      );
    case "tenure_with_unsure":
      return (
        <TenureWithUnsure
          options={question.options ?? []}
          onSelect={(value) => onAnswer(value)}
          disabled={disabled}
        />
      );
    case "currency":
      return (
        <TextInput
          type="currency"
          placeholder={question.placeholder}
          hint={question.hint}
          onSubmit={(value) => onAnswer(Number(value))}
          disabled={disabled}
        />
      );
    case "checkbox_group":
      return (
        <CheckboxGroup
          options={question.options ?? []}
          hint={question.hint}
          onSubmit={(selected) => onAnswer(selected)}
          disabled={disabled}
        />
      );
    case "dual_property_block":
      return (
        <DualPropertyBlock
          tenureOptions={question.tenure_options ?? []}
          onSubmit={(block) => onAnswer(block)}
          disabled={disabled}
        />
      );
    case "optional_postcode":
      return (
        <OptionalPostcode
          placeholder={question.placeholder}
          hint={question.hint}
          onSubmit={(postcode) => onAnswer(postcode)}
          onSkip={() => onAnswer("")}
          disabled={disabled}
        />
      );
    default:
      return null;
  }
}
