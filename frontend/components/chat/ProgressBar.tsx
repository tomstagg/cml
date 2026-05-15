"use client";

export function ProgressBar({ value }: { value: number }) {
  return (
    <div className="w-full bg-surface-muted rounded-full h-2 overflow-hidden">
      <div
        className="h-full rounded-full transition-all duration-500 ease-out"
        style={{
          width: `${Math.min(100, Math.max(0, value))}%`,
          backgroundImage:
            "linear-gradient(90deg, #0AE5F6 0%, #9747FF 60%, #080C64 100%)",
        }}
      />
    </div>
  );
}
