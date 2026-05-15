"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { ProgressBar } from "./ProgressBar";

type Question = {
  id: string;
  step: number;
  text: string;
  type: string;
};

type Props = {
  questions: Question[];
  answers: Record<string, string | string[]>;
  currentStep: number;
  totalSteps: number;
  isComplete: boolean;
};

const FIELD_LABELS: Record<string, string> = {
  purchase_price: "Purchase Price",
  tenure: "Tenure",
  property_postcode: "Property Postcode",
  mortgage: "Mortgage",
  new_build: "New build",
  help_to_buy_isa: "Help to Buy ISA",
  shared_ownership: "Shared Ownership",
  scorecard_preference: "Ranking",
  include_distance: "Include distance",
};

const VALUE_LABELS: Record<string, Record<string, string>> = {
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
    complaints: "Complaints",
    regulatory: "Regulatory",
    distance: "Distance",
    offices: "Offices",
  },
};

function formatAnswer(id: string, raw: string | string[] | undefined): string {
  if (raw === undefined) return "";
  const value = typeof raw === "string" ? raw : raw.join(", ");
  if (id === "purchase_price") {
    const n = Number(String(value).replace(/[^\d.]/g, ""));
    if (Number.isFinite(n) && n > 0) {
      return new Intl.NumberFormat("en-GB", {
        style: "currency",
        currency: "GBP",
        maximumFractionDigits: 0,
      }).format(n);
    }
  }
  return VALUE_LABELS[id]?.[value] ?? value;
}

export function ChatSidebar({
  questions,
  answers,
  currentStep,
  totalSteps,
  isComplete,
}: Props) {
  const answered = questions.filter((q) => q.id in answers);
  const progressPct = isComplete
    ? 100
    : (Math.max(0, Math.min(currentStep - 1, totalSteps)) / totalSteps) * 100;
  const stepLabel = isComplete
    ? `Complete`
    : `Question ${Math.min(currentStep, totalSteps)} of ${totalSteps}`;

  return (
    <aside className="hidden lg:flex flex-col w-72 border-r border-gray-200 bg-white p-6 overflow-y-auto">
      <h2 className="text-h5 font-bold text-navy mb-4">Your progress</h2>

      <div className="flex items-center justify-between text-sm mb-2">
        <span className="text-ink-muted">{stepLabel}</span>
        <span className="font-semibold text-navy">Your quote</span>
      </div>
      <ProgressBar value={progressPct} />

      <h3 className="text-h5 font-bold text-navy mt-8 mb-3">Chat summary</h3>
      <dl className="space-y-2.5 border-t border-gray-200 pt-3">
        {answered.length === 0 && (
          <p className="text-sm text-ink-muted">Your answers will appear here.</p>
        )}
        {answered.map((q) => (
          <div
            key={q.id}
            className="flex items-baseline justify-between gap-3 text-sm"
          >
            <dt className="text-navy">{FIELD_LABELS[q.id] ?? q.id}</dt>
            <dd className="font-semibold text-navy text-right truncate">
              {formatAnswer(q.id, answers[q.id])}
            </dd>
          </div>
        ))}
      </dl>

      <h3 className="text-h5 font-bold text-navy mt-8 mb-3">Extra support</h3>
      <ul className="space-y-2 border-t border-gray-200 pt-3 text-sm">
        <li>
          <Link
            href="/how-it-works"
            className="inline-flex items-center gap-1.5 text-navy hover:text-purple transition-colors"
          >
            <ArrowUpRight className="w-3.5 h-3.5 text-purple" />
            How it works
          </Link>
        </li>
        <li>
          <Link
            href="/contact"
            className="inline-flex items-center gap-1.5 text-navy hover:text-purple transition-colors"
          >
            <ArrowUpRight className="w-3.5 h-3.5 text-purple" />
            Contact support
          </Link>
        </li>
        <li>
          <Link
            href="/conveyancing"
            className="inline-flex items-center gap-1.5 text-navy hover:text-purple transition-colors"
          >
            <ArrowUpRight className="w-3.5 h-3.5 text-purple" />
            Learn about Conveyancing
          </Link>
        </li>
      </ul>
    </aside>
  );
}
