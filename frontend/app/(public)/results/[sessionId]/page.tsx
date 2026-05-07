import type { Metadata } from "next";
import { ResultsClient } from "@/components/results/ResultsClient";

export const metadata: Metadata = {
  title: "Your Conveyancing Quotes",
  description:
    "Compare residential conveyancing solicitors ranked by reputation, price, complaints, regulatory history, distance, and offices.",
};

export default async function ResultsPage({ params }: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await params;
  return <ResultsClient sessionId={sessionId} />;
}
