"use client";

import { ChevronRight } from "lucide-react";

const QUESTION_LABELS: Record<string, string> = {
  service_type: "Service type",
  estate_value: "Estate value",
  has_will: "Valid Will?",
  iht400: "IHT400 required?",
  uk_domiciled: "UK domiciled?",
  uk_property_count: "UK properties",
  bank_account_count: "Bank accounts",
  investments_count: "Investments",
  overseas_assets: "Overseas assets?",
  beneficiary_count: "Beneficiaries",
  location: "Postcode",
  location_preference: "Location pref.",
  ranking_preference: "Ranked by",
};

const ANSWER_LABELS: Record<string, Record<string, string>> = {
  service_type: { grant_only: "Grant only", full_administration: "Full administration" },
  estate_value: {
    under_100k: "Under £100k",
    "100k_325k": "£100k – £325k",
    "325k_650k": "£325k – £650k",
    "650k_1m": "£650k – £1m",
    over_1m: "Over £1m",
  },
  has_will: { yes: "Yes", no: "No (intestacy)", unknown: "Not sure" },
  iht400: { yes: "Yes", no: "No", unknown: "Not sure" },
  uk_domiciled: { yes: "Yes", no: "No", unknown: "Not sure" },
  uk_property_count: { "0": "None", "1": "1", "2": "2", "3plus": "3+" },
  bank_account_count: { "0": "None", "1_3": "1 – 3", "4_6": "4 – 6", "7plus": "7+" },
  investments_count: { none: "None", simple: "Simple", complex: "Complex" },
  overseas_assets: { yes: "Yes", no: "No" },
  beneficiary_count: { "1_2": "1 – 2", "3_5": "3 – 5", "6plus": "6+" },
  location_preference: { local: "Local", remote: "Remote", no_preference: "No preference" },
  ranking_preference: { price: "Price", reputation: "Reviews", distance: "Location", balanced: "Balanced" },
};

type Props = {
  answers: Record<string, string | string[]>;
};

export function AnswerSidebar({ answers }: Props) {
  const answered = Object.entries(answers);

  if (answered.length === 0) {
    return (
      <aside className="hidden lg:block w-64 border-r border-gray-200 bg-white p-4">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
          Your Answers
        </h2>
        <p className="text-sm text-gray-400">Answers will appear here as you go.</p>
      </aside>
    );
  }

  return (
    <aside className="hidden lg:block w-64 border-r border-gray-200 bg-white p-4 overflow-y-auto">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
        Your Answers
      </h2>
      <ul className="space-y-2">
        {answered.map(([questionId, answer]) => {
          const label = QUESTION_LABELS[questionId] ?? questionId;
          const answerStr = typeof answer === "string" ? answer : answer.join(", ");
          const displayAnswer =
            ANSWER_LABELS[questionId]?.[answerStr] ?? answerStr;

          return (
            <li key={questionId} className="text-sm">
              <span className="text-gray-400 text-xs">{label}</span>
              <div className="flex items-center gap-1 text-gray-700 font-medium">
                <ChevronRight className="w-3 h-3 text-brand-400 flex-shrink-0" />
                {displayAnswer}
              </div>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
