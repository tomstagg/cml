"use client";

type Props = {
  count: number;
  max: number;
  onOpen: () => void;
};

export function CallbackStickyBar({ count, max, onOpen }: Props) {
  if (count === 0) return null;
  return (
    <div className="fixed inset-x-0 bottom-0 z-40 bg-white border-t border-gray-200 shadow-lg">
      <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
        <p className="text-sm text-navy" aria-live="polite">
          {count} firm{count === 1 ? "" : "s"} selected for callback (max {max})
        </p>
        <button onClick={onOpen} className="btn-primary">
          Request callbacks ({count}/{max})
        </button>
      </div>
    </div>
  );
}
