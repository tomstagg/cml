"use client";

import { useState } from "react";
import { ArrowRight } from "lucide-react";

type InputType = "currency" | "text" | "email" | "tel";

type Props = {
  type: InputType;
  placeholder?: string;
  hint?: string;
  onSubmit: (value: string) => void;
  disabled?: boolean;
};

const EMAIL_REGEX = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const PHONE_REGEX = /^[+\d][\d\s]{8,}$/;

function validate(type: InputType, value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return "This field is required.";

  if (type === "currency") {
    const numeric = Number(trimmed.replace(/[£,\s]/g, ""));
    if (!Number.isFinite(numeric)) return "Please enter a numeric amount.";
    if (numeric <= 0) return "Amount must be greater than zero.";
  }

  if (type === "email" && !EMAIL_REGEX.test(trimmed)) {
    return "Please enter a valid email address.";
  }

  if (type === "tel") {
    const cleaned = trimmed.replace(/\s/g, "");
    if (!PHONE_REGEX.test(cleaned)) return "Please enter a valid phone number.";
  }

  return null;
}

function normalise(type: InputType, value: string): string {
  const trimmed = value.trim();
  if (type === "currency") {
    return String(Number(trimmed.replace(/[£,\s]/g, "")));
  }
  return trimmed;
}

export function TextInput({ type, placeholder, hint, onSubmit, disabled }: Props) {
  const [value, setValue] = useState("");
  const [error, setError] = useState("");

  function handleSubmit() {
    const validationError = validate(type, value);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError("");
    onSubmit(normalise(type, value));
  }

  const inputType = type === "tel" ? "tel" : type === "email" ? "email" : "text";

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          type={inputType}
          inputMode={type === "currency" ? "decimal" : type === "tel" ? "tel" : "text"}
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            setError("");
          }}
          placeholder={placeholder}
          className="input flex-1 max-w-md"
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
      {hint && <p className="text-xs text-gray-500">{hint}</p>}
    </div>
  );
}
