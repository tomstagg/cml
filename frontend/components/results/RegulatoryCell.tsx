"use client";

import { SeverityCell } from "./SeverityCell";

type Props = {
  score: number;
  sourceUrl: string | null;
  compact?: boolean;
};

export function RegulatoryCell({ score, sourceUrl, compact }: Props) {
  return (
    <SeverityCell
      score={score}
      sourceUrl={sourceUrl}
      ariaLabel="regulatory history"
      compact={compact}
    />
  );
}
