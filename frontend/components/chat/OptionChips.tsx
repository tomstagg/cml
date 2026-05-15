"use client";

import { cn } from "@/lib/utils";

type Option = {
  value: string;
  label: string;
  description?: string;
};

type Props = {
  options: Option[];
  onSelect: (value: string) => void;
  disabled?: boolean;
};

export function OptionChips({ options, onSelect, disabled }: Props) {
  const hasDescriptions = options.some((o) => o.description);

  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => onSelect(option.value)}
          disabled={disabled}
          className={cn(
            "border border-navy bg-white text-navy text-sm font-medium",
            "transition-colors hover:bg-navy hover:text-white",
            "focus:outline-none focus-visible:ring-2 focus-visible:ring-purple focus-visible:ring-offset-1",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            hasDescriptions
              ? "flex flex-col items-start gap-0.5 rounded-2xl px-5 py-3 text-left max-w-xs"
              : "rounded-full px-4 py-1.5",
          )}
          type="button"
        >
          <span>{option.label}</span>
          {option.description && (
            <span className="text-xs font-normal text-ink-muted hover:text-white/80">
              {option.description}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
