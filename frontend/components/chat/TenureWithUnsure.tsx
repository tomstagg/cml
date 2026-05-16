"use client";

import { useState } from "react";
import { Info } from "lucide-react";
import { cn } from "@/lib/utils";

type Option = { value: string; label: string };

type Props = {
  options: Option[];
  onSelect: (value: string) => void;
  disabled?: boolean;
};

const EXPLAINER = (
  <>
    <p className="font-medium text-navy text-sm mb-2">Freehold or leasehold?</p>
    <p className="text-xs text-ink-muted mb-2">
      <strong>Freehold</strong> means you own the property and the land it stands on outright,
      with no time limit. Most houses in England and Wales are freehold.
    </p>
    <p className="text-xs text-ink-muted">
      <strong>Leasehold</strong> means you own the property for a fixed term (often 99-999 years)
      under a lease from the freeholder. Most flats are leasehold; some new-build houses are too.
      Your sale or purchase contract, or the title deeds, will say which applies.
    </p>
  </>
);

export function TenureWithUnsure({ options, onSelect, disabled }: Props) {
  const [showExplainer, setShowExplainer] = useState(false);

  function handleClick(value: string) {
    if (value === "unsure") {
      setShowExplainer(true);
      return;
    }
    setShowExplainer(false);
    onSelect(value);
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <button
            key={option.value}
            onClick={() => handleClick(option.value)}
            disabled={disabled}
            className={cn(
              "rounded-full border border-navy bg-white px-4 py-1.5 text-sm font-medium text-navy",
              "transition-colors hover:bg-navy hover:text-white",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-purple focus-visible:ring-offset-1",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              option.value === "unsure" && showExplainer && "bg-navy/10",
            )}
            type="button"
          >
            {option.label}
          </button>
        ))}
      </div>

      {showExplainer && (
        <div className="rounded-lg border border-purple/20 bg-purple/5 p-3 max-w-md">
          <div className="flex gap-2">
            <Info className="w-4 h-4 text-purple flex-shrink-0 mt-0.5" />
            <div>{EXPLAINER}</div>
          </div>
          <p className="text-xs text-ink-muted mt-3">
            Once you know, pick Freehold or Leasehold above to continue.
          </p>
        </div>
      )}
    </div>
  );
}
