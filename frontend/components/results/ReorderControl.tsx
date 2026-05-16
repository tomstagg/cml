"use client";

import { ChevronDown, MapPin } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const SCORECARDS: { value: string; label: string; description: string }[] = [
  { value: "balanced", label: "Balanced", description: "Blend of all factors" },
  { value: "reputation", label: "Reputation", description: "Best reviews first" },
  { value: "price", label: "Price", description: "Lowest cost first" },
  { value: "complaints", label: "Complaints history", description: "Cleanest LeO record first" },
  { value: "regulatory", label: "Regulatory history", description: "Cleanest SRA record first" },
  { value: "distance", label: "Distance", description: "Closest firms first" },
  { value: "offices", label: "Number of offices", description: "Larger firms first" },
];

type Props = {
  scorecard: string;
  includeDistance: boolean;
  hasPostcode: boolean;
  onChange: (next: { scorecard: string; includeDistance: boolean }) => void;
  disabled?: boolean;
};

export function ReorderControl({
  scorecard,
  includeDistance,
  hasPostcode,
  onChange,
  disabled,
}: Props) {
  const [open, setOpen] = useState(false);

  return (
    <div className="card p-4 flex flex-wrap items-center gap-3 mb-4">
      <p className="text-sm font-semibold text-navy mr-2">Re-order your search results?</p>

      <div className="relative">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          disabled={disabled}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border border-navy/30 bg-white px-3 py-1.5 text-sm font-medium text-navy",
            "hover:border-navy disabled:opacity-50",
          )}
        >
          {SCORECARDS.find((s) => s.value === scorecard)?.label ?? "Balanced"}
          <ChevronDown className="w-3.5 h-3.5" />
        </button>
        {open && (
          <div className="absolute left-0 z-10 mt-1 w-72 rounded-xl border border-gray-200 bg-white shadow-lg p-1">
            {SCORECARDS.map((s) => (
              <button
                key={s.value}
                type="button"
                onClick={() => {
                  setOpen(false);
                  onChange({ scorecard: s.value, includeDistance });
                }}
                className={cn(
                  "w-full text-left rounded-lg px-3 py-2 text-sm hover:bg-navy/5",
                  s.value === scorecard && "bg-navy/5",
                )}
              >
                <div className="font-medium text-navy">{s.label}</div>
                <div className="text-xs text-ink-muted">{s.description}</div>
              </button>
            ))}
          </div>
        )}
      </div>

      {hasPostcode && (
        <button
          type="button"
          onClick={() => onChange({ scorecard, includeDistance: !includeDistance })}
          disabled={disabled}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
            includeDistance
              ? "border border-navy bg-navy text-white"
              : "border border-navy/30 bg-white text-navy hover:border-navy",
            "disabled:opacity-50",
          )}
        >
          <MapPin className="w-3.5 h-3.5" />
          {includeDistance ? "Distance: on" : "Distance: off"}
        </button>
      )}
    </div>
  );
}
