import type { Metadata } from "next";
import { ResultsClient } from "@/components/results/ResultsClient";

export const metadata: Metadata = {
  title: "Your Probate Solicitor Comparison",
  description: "Compare probate solicitors ranked by price, reputation, and distance.",
};

export default function ResultsPage({ params }: { params: { sessionId: string } }) {
  return <ResultsClient sessionId={params.sessionId} />;
}
