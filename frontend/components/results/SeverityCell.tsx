"use client";

import { Star, ExternalLink } from "lucide-react";
import { cn, severityBand } from "@/lib/utils";

type Props = {
  score: number;
  sourceUrl: string | null;
  /** Used for the "View source" link's accessible name, e.g. "complaints history". */
  ariaLabel: string;
  /** Compact variant tightens the layout for the full results table. */
  compact?: boolean;
};

export function SeverityCell({ score, sourceUrl, ariaLabel, compact }: Props) {
  const { stars, label } = severityBand(score);

  return (
    <div className={cn("flex flex-col items-start gap-0.5", compact && "gap-0")}>
      <div
        className="flex items-center gap-0.5"
        role="img"
        aria-label={`${stars} out of 5 — ${label} ${ariaLabel}`}
      >
        {Array.from({ length: 5 }).map((_, i) => (
          <Star
            key={i}
            className={cn(
              compact ? "w-3.5 h-3.5" : "w-4 h-4",
              i < stars ? "text-teal fill-teal" : "text-gray-300",
            )}
          />
        ))}
      </div>
      <span className={cn("font-medium text-navy", compact ? "text-xs" : "text-sm")}>
        {label}
      </span>
      {sourceUrl && (
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-purple hover:underline inline-flex items-center gap-0.5"
        >
          View source <ExternalLink className="w-3 h-3" />
        </a>
      )}
    </div>
  );
}
