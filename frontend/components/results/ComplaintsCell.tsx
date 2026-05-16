"use client";

import { SeverityCell } from "./SeverityCell";

type Props = {
  score: number;
  sourceUrl: string | null;
  compact?: boolean;
};

export function ComplaintsCell({ score, sourceUrl, compact }: Props) {
  return (
    <SeverityCell
      score={score}
      sourceUrl={sourceUrl}
      ariaLabel="complaints history"
      compact={compact}
    />
  );
}
