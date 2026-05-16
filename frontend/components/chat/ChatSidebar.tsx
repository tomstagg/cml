"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { ProgressBar } from "./ProgressBar";

type Question = {
  id: string;
  step: number;
  text: string;
  type: string;
  pathways?: string[];
};

type Props = {
  questions: Question[];
  answers: Record<string, unknown>;
  pathway: string | null;
  currentStep: number;
  isComplete: boolean;
};

const FIELD_LABELS: Record<string, string> = {
  transaction_type: "Transaction",
  purchase_tenure_type: "Purchase tenure",
  purchase_property_value: "Purchase price",
  sale_tenure_type: "Sale tenure",
  sale_property_value: "Sale price",
  combined_property_details: "Properties",
  transaction_details: "Transaction details",
  distance_preference: "Postcode",
};

const VALUE_LABELS: Record<string, Record<string, string>> = {
  transaction_type: {
    buying: "Buying",
    selling: "Selling",
    selling_and_buying: "Selling & buying",
  },
  purchase_tenure_type: { freehold: "Freehold", leasehold: "Leasehold", unsure: "Not sure" },
  sale_tenure_type: { freehold: "Freehold", leasehold: "Leasehold", unsure: "Not sure" },
};

const MODIFIER_LABELS: Record<string, string> = {
  mortgage_required: "Mortgage",
  new_build: "New build",
  new_lease: "New lease",
  shared_ownership_or_help_to_buy: "Shared ownership / HtB",
  gifted_deposit: "Gifted deposit",
  unregistered_title_purchase: "Unregistered (buying)",
  unregistered_title_sale: "Unregistered (selling)",
  additional_mortgage_redemption: "Additional mortgage",
};

function formatPounds(value: number | string): string {
  const n = typeof value === "number" ? value : Number(String(value).replace(/[^\d.]/g, ""));
  if (!Number.isFinite(n) || n <= 0) return String(value ?? "");
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 0,
  }).format(n);
}

function formatAnswer(id: string, raw: unknown): string {
  if (raw === undefined || raw === null || raw === "") return "—";

  if (id === "purchase_property_value" || id === "sale_property_value") {
    return formatPounds(raw as number | string);
  }
  if (id === "combined_property_details" && typeof raw === "object" && raw !== null) {
    const block = raw as Record<string, unknown>;
    return `Buying ${formatPounds(block.purchase_property_value as number)}, selling ${formatPounds(
      block.sale_property_value as number,
    )}`;
  }
  if (id === "transaction_details" && Array.isArray(raw)) {
    if (raw.length === 0) return "None selected";
    return raw.map((v) => MODIFIER_LABELS[v] ?? v).join(", ");
  }
  if (id === "distance_preference") {
    return raw ? String(raw) : "Skipped";
  }
  if (typeof raw === "string") {
    return VALUE_LABELS[id]?.[raw] ?? raw;
  }
  return String(raw);
}

export function ChatSidebar({ questions, answers, pathway, currentStep, isComplete }: Props) {
  const pathwayQuestions = pathway
    ? questions.filter((q) => q.pathways?.includes(pathway))
    : questions.filter((q) => q.id === "transaction_type");
  const totalSteps = pathwayQuestions.length || 5;

  const answered = pathwayQuestions.filter((q) => q.id in answers);
  const progressPct = isComplete
    ? 100
    : (Math.max(0, Math.min(currentStep - 1, totalSteps)) / totalSteps) * 100;
  const stepLabel = isComplete
    ? "Complete"
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
          <div key={q.id} className="flex items-baseline justify-between gap-3 text-sm">
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
