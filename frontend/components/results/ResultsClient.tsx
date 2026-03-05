"use client";

import { useEffect, useState } from "react";
import { Loader2, ArrowLeft, SortAsc } from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { searchApi } from "@/lib/api";
import { FirmCard } from "./FirmCard";
import { AppointModal } from "./AppointModal";
import { CallbackModal } from "./CallbackModal";
import { cn } from "@/lib/utils";

type QuoteBreakdown = {
  base_fee: number;
  adjustments: { name: string; amount: number }[];
  fees_subtotal: number;
  vat: number;
  disbursements: { name: string; amount: number; estimated: boolean }[];
  disbursements_total: number;
  total: number;
  currency: string;
  pricing_model: string;
};

type FirmResult = {
  rank: number;
  org_id: string;
  name: string;
  sra_number: string;
  auth_status: string;
  enrolled: boolean;
  website_url: string | null;
  aggregate_rating: number | null;
  aggregate_review_count: number | null;
  postcode: string | null;
  city: string | null;
  distance_km: number | null;
  quote: QuoteBreakdown | null;
  score: number;
};

type SortKey = "rank" | "price" | "reputation" | "distance";

const SORT_LABELS: Record<SortKey, string> = {
  rank: "Best Match",
  price: "Price",
  reputation: "Best Reviewed",
  distance: "Nearest",
};

export function ResultsClient({ sessionId }: { sessionId: string }) {
  const router = useRouter();
  const [results, setResults] = useState<FirmResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<SortKey>("rank");
  const [appointFirm, setAppointFirm] = useState<FirmResult | null>(null);
  const [callbackFirm, setCallbackFirm] = useState<FirmResult | null>(null);

  useEffect(() => {
    loadResults();
  }, []);

  async function loadResults() {
    try {
      const data = await searchApi.getResults(sessionId) as { results: FirmResult[] };
      setResults(data.results);
    } catch (err: any) {
      if (err.status === 400) {
        toast.error("Please complete the questionnaire first.");
        router.push(`/chat?session=${sessionId}`);
      } else {
        toast.error("Failed to load results. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  const sorted = [...results].sort((a, b) => {
    switch (sortBy) {
      case "price":
        return (a.quote?.total ?? Infinity) - (b.quote?.total ?? Infinity);
      case "reputation":
        return (b.aggregate_rating ?? 0) - (a.aggregate_rating ?? 0);
      case "distance":
        return (a.distance_km ?? Infinity) - (b.distance_km ?? Infinity);
      default:
        return a.rank - b.rank;
    }
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-64px)]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-brand-600 animate-spin mx-auto mb-3" />
          <p className="text-gray-500">Finding the best solicitors for you...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="py-8 px-4 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <button
            onClick={() => router.push(`/chat?session=${sessionId}`)}
            className="btn-ghost text-sm mb-2"
          >
            <ArrowLeft className="w-4 h-4" /> Revise answers
          </button>
          <h1 className="text-2xl font-bold text-gray-900">
            {results.length} solicitors found
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Ranked by price (60%), reviews (25%), and distance (15%)
          </p>
        </div>

        {/* Sort controls */}
        <div className="hidden sm:flex items-center gap-2 flex-wrap">
          <span className="text-sm text-gray-500 flex items-center gap-1">
            <SortAsc className="w-4 h-4" /> Sort:
          </span>
          {(Object.keys(SORT_LABELS) as SortKey[]).map((key) => (
            <button
              key={key}
              onClick={() => setSortBy(key)}
              className={cn(
                "text-sm px-3 py-1.5 rounded-lg font-medium border transition-colors",
                sortBy === key
                  ? "bg-brand-600 text-white border-brand-600"
                  : "bg-white text-gray-600 border-gray-300 hover:border-brand-400",
              )}
            >
              {SORT_LABELS[key]}
            </button>
          ))}
        </div>
      </div>

      {results.length === 0 ? (
        <div className="text-center py-16 card">
          <p className="text-gray-500 mb-4">
            No enrolled solicitors found matching your criteria yet.
          </p>
          <p className="text-gray-400 text-sm">
            We're growing our network — please check back soon.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {sorted.map((firm) => (
            <FirmCard
              key={firm.org_id}
              firm={firm}
              onAppoint={() => setAppointFirm(firm)}
              onCallback={() => setCallbackFirm(firm)}
            />
          ))}
        </div>
      )}

      {/* Regulatory notice */}
      <p className="text-xs text-gray-400 text-center mt-8 max-w-2xl mx-auto">
        All firms are checked against the SRA register. Quotes are estimates and may vary — final
        fees are agreed directly with your solicitor. Choose My Lawyer is not regulated by the SRA.
      </p>

      {/* Modals */}
      {appointFirm && (
        <AppointModal
          firm={appointFirm}
          sessionId={sessionId}
          onClose={() => setAppointFirm(null)}
        />
      )}
      {callbackFirm && (
        <CallbackModal
          firm={callbackFirm}
          sessionId={sessionId}
          onClose={() => setCallbackFirm(null)}
        />
      )}
    </div>
  );
}
