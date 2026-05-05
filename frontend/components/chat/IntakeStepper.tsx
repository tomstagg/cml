"use client";

import { Check, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

type Question = {
  id: string;
  step: number;
  section?: string;
  text: string;
  type: string;
};

type Props = {
  questions: Question[];
  currentQuestionId: string | null;
  answers: Record<string, string | string[]>;
  onEditStep?: (questionId: string) => void;
};

const FALLBACK_LABELS: Record<string, string> = {
  purchase_price: "Purchase price",
  tenure: "Tenure",
  property_postcode: "Property postcode",
  mortgage: "Mortgage",
  new_build: "New build",
  help_to_buy_isa: "Help to Buy ISA",
  shared_ownership: "Shared ownership",
  scorecard_preference: "Ranking preference",
  include_distance: "Include distance",
  first_name: "First name",
  last_name: "Last name",
  email: "Email",
  phone: "Phone",
};

const ANSWER_LABELS: Record<string, Record<string, string>> = {
  tenure: { freehold: "Freehold", leasehold: "Leasehold", unknown: "Not sure" },
  mortgage: { yes: "Yes", no: "No" },
  new_build: { yes: "Yes", no: "No" },
  help_to_buy_isa: { yes: "Yes", no: "No" },
  shared_ownership: { yes: "Yes", no: "No" },
  include_distance: { yes: "Yes", no: "No" },
  scorecard_preference: {
    balanced: "Balanced",
    reputation: "Reputation",
    price: "Price",
    complaints: "Complaints record",
    regulatory: "Regulatory record",
    distance: "Distance",
    offices: "Offices",
  },
};

function formatAnswer(questionId: string, raw: string | string[] | undefined): string {
  if (raw === undefined) return "";
  const value = typeof raw === "string" ? raw : raw.join(", ");
  if (questionId === "purchase_price") {
    const numeric = Number(String(value).replace(/[^\d.]/g, ""));
    if (Number.isFinite(numeric) && numeric > 0) {
      return new Intl.NumberFormat("en-GB", {
        style: "currency",
        currency: "GBP",
        maximumFractionDigits: 0,
      }).format(numeric);
    }
  }
  return ANSWER_LABELS[questionId]?.[value] ?? value;
}

export function IntakeStepper({ questions, currentQuestionId, answers, onEditStep }: Props) {
  const sections = questions.reduce<Record<string, Question[]>>((acc, q) => {
    const key = q.section ?? "Your enquiry";
    if (!acc[key]) acc[key] = [];
    acc[key].push(q);
    return acc;
  }, {});

  return (
    <aside className="hidden lg:flex flex-col w-72 border-r border-gray-200 bg-white p-5 overflow-y-auto">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-4">
        Your progress
      </h2>

      <ol className="space-y-6">
        {Object.entries(sections).map(([sectionName, sectionQuestions]) => (
          <li key={sectionName}>
            <p className="text-[11px] font-semibold text-brand-700 uppercase tracking-wide mb-2">
              {sectionName}
            </p>
            <ul className="space-y-2">
              {sectionQuestions.map((q) => {
                const isAnswered = q.id in answers;
                const isActive = q.id === currentQuestionId;
                const label = FALLBACK_LABELS[q.id] ?? q.id;
                const answerSummary = isAnswered ? formatAnswer(q.id, answers[q.id]) : "";
                const editable = isAnswered && Boolean(onEditStep);

                const content = (
                  <>
                    <span
                      className={cn(
                        "flex-shrink-0 mt-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center text-[10px] font-semibold",
                        isAnswered
                          ? "bg-brand-600 border-brand-600 text-white"
                          : isActive
                            ? "border-brand-500 text-brand-700"
                            : "border-gray-300 text-gray-400",
                      )}
                    >
                      {isAnswered ? <Check className="w-3 h-3" /> : q.step}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p
                        className={cn(
                          "text-sm leading-tight",
                          isActive ? "text-gray-900 font-medium" : "text-gray-700",
                        )}
                      >
                        {label}
                      </p>
                      {answerSummary && (
                        <p className="flex items-center gap-1 text-xs text-gray-500 truncate">
                          <ChevronRight className="w-3 h-3 text-brand-400 flex-shrink-0" />
                          <span className="truncate">{answerSummary}</span>
                        </p>
                      )}
                      {editable && (
                        <p className="text-[10px] text-brand-600 font-medium uppercase tracking-wide mt-0.5">
                          Edit
                        </p>
                      )}
                    </div>
                  </>
                );

                const baseClasses = cn(
                  "flex items-start gap-2 rounded-lg px-2 py-1.5 transition-colors w-full text-left",
                  isActive && "bg-brand-50",
                  editable && "hover:bg-gray-50 cursor-pointer focus:outline-none focus:ring-2 focus:ring-brand-500",
                );

                return (
                  <li key={q.id}>
                    {editable && onEditStep ? (
                      <button
                        type="button"
                        onClick={() => onEditStep(q.id)}
                        className={baseClasses}
                      >
                        {content}
                      </button>
                    ) : (
                      <div className={baseClasses}>{content}</div>
                    )}
                  </li>
                );
              })}
            </ul>
          </li>
        ))}
      </ol>
    </aside>
  );
}
