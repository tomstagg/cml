import type { Metadata } from "next";
import { ResultsClient } from "@/components/results/ResultsClient";

export const metadata: Metadata = {
  title: "Your Probate Solicitor Comparison",
  description: "Compare probate solicitors ranked by price, reputation, and distance.",
};

export default async function ResultsPage({ params }: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await params;
  return <ResultsClient sessionId={sessionId} />;
}
