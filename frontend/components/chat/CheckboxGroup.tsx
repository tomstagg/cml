"use client";

import { useState } from "react";
import { ArrowRight, Check, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

type Option = { value: string; label: string; description?: string | null };

type Props = {
  options: Option[];
  onSubmit: (selected: string[]) => void;
  hint?: string;
  disabled?: boolean;
};

export function CheckboxGroup({ options, onSubmit, hint, disabled }: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  function toggle(value: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(value)) {
        next.delete(value);
      } else {
        next.add(value);
      }
      return next;
    });
  }

  function toggleExpand(value: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return next;
    });
  }

  function handleContinue() {
    onSubmit(Array.from(selected));
  }

  return (
    <div className="space-y-3 max-w-xl">
      <div className="flex flex-col gap-2">
        {options.map((option) => {
          const isSelected = selected.has(option.value);
          const isExpanded = expanded.has(option.value);
          const hasExplainer = Boolean(option.description);
          return (
            <div
              key={option.value}
              className={cn(
                "rounded-xl border transition-colors",
                "focus-within:ring-2 focus-within:ring-purple focus-within:ring-offset-1",
                isSelected
                  ? "border-navy bg-navy text-white"
                  : "border-navy/20 bg-white text-navy",
              )}
            >
              <div className="flex items-stretch">
                <button
                  type="button"
                  onClick={() => toggle(option.value)}
                  disabled={disabled}
                  className={cn(
                    "flex flex-1 items-center gap-3 rounded-l-xl px-4 py-3 text-left text-sm font-medium",
                    "disabled:opacity-50 disabled:cursor-not-allowed",
                    !isSelected && "hover:bg-navy/[0.03]",
                  )}
                >
                  <span
                    className={cn(
                      "flex h-5 w-5 items-center justify-center rounded border flex-shrink-0",
                      isSelected ? "border-white bg-white" : "border-navy/40 bg-white",
                    )}
                  >
                    {isSelected && <Check className="h-3.5 w-3.5 text-navy" strokeWidth={3} />}
                  </span>
                  <span className="flex-1">{option.label}</span>
                </button>
                {hasExplainer && (
                  <button
                    type="button"
                    onClick={() => toggleExpand(option.value)}
                    disabled={disabled}
                    aria-expanded={isExpanded}
                    aria-label={isExpanded ? "Hide explanation" : "What does this mean?"}
                    className={cn(
                      "px-3 rounded-r-xl text-xs font-medium border-l flex items-center gap-1",
                      "disabled:opacity-50",
                      isSelected
                        ? "border-white/20 text-white/90 hover:bg-white/10"
                        : "border-navy/10 text-purple hover:bg-purple/5",
                    )}
                  >
                    <span className="hidden sm:inline">
                      {isExpanded ? "Hide" : "What's this?"}
                    </span>
                    <ChevronDown
                      className={cn(
                        "w-3.5 h-3.5 transition-transform",
                        isExpanded && "rotate-180",
                      )}
                    />
                  </button>
                )}
              </div>
              {hasExplainer && isExpanded && (
                <div
                  className={cn(
                    "border-t px-4 py-3 text-xs leading-relaxed",
                    isSelected
                      ? "border-white/20 text-white/85"
                      : "border-navy/10 bg-navy/[0.02] text-ink-muted",
                  )}
                >
                  {option.description}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {hint && <p className="text-xs text-ink-muted">{hint}</p>}

      <button
        type="button"
        onClick={handleContinue}
        disabled={disabled}
        className="btn-primary px-4 py-2 disabled:opacity-50"
      >
        Continue
        <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
}
