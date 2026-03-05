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
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => onSelect(option.value)}
          disabled={disabled}
          className={cn(
            "flex flex-col items-start px-4 py-2.5 rounded-xl border-2 text-sm font-medium transition-all",
            "border-brand-200 text-brand-700 bg-brand-50 hover:bg-brand-100 hover:border-brand-400",
            "focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-1",
            "disabled:opacity-50 disabled:cursor-not-allowed",
          )}
          type="button"
        >
          <span>{option.label}</span>
          {option.description && (
            <span className="text-xs text-gray-500 font-normal mt-0.5">{option.description}</span>
          )}
        </button>
      ))}
    </div>
  );
}
