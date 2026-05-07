"use client";

import type { DecisionSource } from "@/lib/api";
import { SeverityCell } from "./SeverityCell";

type Props = {
  score: number;
  sources: DecisionSource[];
  compact?: boolean;
};

export function ComplaintsCell({ score, sources, compact }: Props) {
  return (
    <SeverityCell
      score={score}
      sources={sources}
      ariaLabel="complaints history"
      compact={compact}
    />
  );
}
