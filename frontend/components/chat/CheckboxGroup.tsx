"use client";

import { useState } from "react";
import { ArrowRight, Check } from "lucide-react";
import { cn } from "@/lib/utils";

type Option = { value: string; label: string };

type Props = {
  options: Option[];
  onSubmit: (selected: string[]) => void;
  hint?: string;
  disabled?: boolean;
};

export function CheckboxGroup({ options, onSubmit, hint, disabled }: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set());

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

  function handleContinue() {
    onSubmit(Array.from(selected));
  }

  return (
    <div className="space-y-3 max-w-xl">
      <div className="flex flex-col gap-2">
        {options.map((option) => {
          const isSelected = selected.has(option.value);
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => toggle(option.value)}
              disabled={disabled}
              className={cn(
                "flex items-center gap-3 rounded-xl border px-4 py-3 text-left text-sm font-medium transition-colors",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-purple focus-visible:ring-offset-1",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                isSelected
                  ? "border-navy bg-navy text-white"
                  : "border-navy/20 bg-white text-navy hover:border-navy",
              )}
            >
              <span
                className={cn(
                  "flex h-5 w-5 items-center justify-center rounded border",
                  isSelected ? "border-white bg-white" : "border-navy/40 bg-white",
                )}
              >
                {isSelected && <Check className="h-3.5 w-3.5 text-navy" strokeWidth={3} />}
              </span>
              <span className="flex-1">{option.label}</span>
            </button>
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
