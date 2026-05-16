"use client";

import { useState } from "react";
import { ArrowRight } from "lucide-react";

type Props = {
  placeholder?: string;
  hint?: string;
  onSubmit: (postcode: string) => void;
  onSkip: () => void;
  disabled?: boolean;
};

const POSTCODE_REGEX = /^[A-Z]{1,2}[0-9][0-9A-Z]?\s*[0-9][A-Z]{2}$/i;

export function OptionalPostcode({
  placeholder = "e.g. B1 1AA",
  hint,
  onSubmit,
  onSkip,
  disabled,
}: Props) {
  const [value, setValue] = useState("");
  const [error, setError] = useState("");

  function handleSubmit() {
    const trimmed = value.trim().toUpperCase();
    if (!POSTCODE_REGEX.test(trimmed)) {
      setError("Please enter a valid UK postcode, or skip to continue.");
      return;
    }
    setError("");
    onSubmit(trimmed);
  }

  return (
    <div className="space-y-2 max-w-md">
      <div className="flex gap-2">
        <input
          type="text"
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            setError("");
          }}
          placeholder={placeholder}
          className="input flex-1 uppercase"
          maxLength={8}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          disabled={disabled}
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className="btn-primary px-4 py-2"
          type="button"
        >
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <div className="flex items-center justify-between text-xs text-ink-muted">
        {hint && <span>{hint}</span>}
        <button
          onClick={onSkip}
          disabled={disabled}
          className="text-purple underline hover:no-underline ml-auto"
          type="button"
        >
          Skip — show results without distance
        </button>
      </div>
    </div>
  );
}
