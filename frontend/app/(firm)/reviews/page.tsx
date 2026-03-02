"use client";

import { useEffect, useState } from "react";
import { Loader2, Star, Flag, MessageSquare } from "lucide-react";
import { firmReviewsApi } from "@/lib/api";
import { getStoredToken } from "@/lib/utils";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

type Review = {
  id: string;
  source: string;
  rating: number;
  text: string | null;
  reviewer_name: string | null;
  firm_response: string | null;
  firm_response_at: string | null;
  created_at: string;
  reported: boolean;
};

export default function ReviewsPage() {
  const router = useRouter();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [responding, setResponding] = useState<string | null>(null);
  const [responseText, setResponseText] = useState("");

  useEffect(() => {
    const token = getStoredToken();
    if (!token) { router.push("/login"); return; }
    firmReviewsApi.list(token)
      .then((data) => setReviews(data as Review[]))
      .catch(() => router.push("/login"))
      .finally(() => setLoading(false));
  }, []);

  async function handleRespond(reviewId: string) {
    const token = getStoredToken();
    if (!token || !responseText.trim()) return;
    await firmReviewsApi.respond(token, reviewId, responseText.trim());
    setReviews((prev) => prev.map((r) => r.id === reviewId ? { ...r, firm_response: responseText.trim() } : r));
    setResponding(null);
    setResponseText("");
    toast.success("Response submitted");
  }

  async function handleReport(reviewId: string) {
    const token = getStoredToken();
    if (!token) return;
    if (!confirm("Report this review for admin review?")) return;
    await firmReviewsApi.report(token, reviewId, "Reported by firm");
    setReviews((prev) => prev.map((r) => r.id === reviewId ? { ...r, reported: true } : r));
    toast.success("Review reported");
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-brand-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Reviews</h1>

      {reviews.length === 0 ? (
        <div className="card p-12 text-center text-gray-400">
          No reviews yet. Reviews appear after clients complete their matter.
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map((review) => (
            <div key={review.id} className="card p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="flex">
                      {[1, 2, 3, 4, 5].map((s) => (
                        <Star
                          key={s}
                          className={`w-4 h-4 ${s <= review.rating ? "text-amber-400 fill-amber-400" : "text-gray-200"}`}
                        />
                      ))}
                    </div>
                    <span className="text-sm font-medium text-gray-700">
                      {review.reviewer_name || "Anonymous"}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 capitalize">
                      {review.source}
                    </span>
                  </div>
                  {review.text && <p className="text-gray-700 text-sm">{review.text}</p>}
                  <p className="text-xs text-gray-400 mt-2">
                    {new Date(review.created_at).toLocaleDateString("en-GB")}
                  </p>

                  {/* Existing response */}
                  {review.firm_response && (
                    <div className="mt-3 pl-3 border-l-2 border-brand-200">
                      <p className="text-xs text-brand-700 font-medium mb-1">Your response:</p>
                      <p className="text-sm text-gray-600">{review.firm_response}</p>
                    </div>
                  )}

                  {/* Response form */}
                  {responding === review.id && (
                    <div className="mt-3">
                      <textarea
                        value={responseText}
                        onChange={(e) => setResponseText(e.target.value)}
                        className="input text-sm min-h-[80px] resize-none"
                        placeholder="Write your response... (max 500 characters)"
                        maxLength={500}
                        autoFocus
                      />
                      <div className="flex gap-2 mt-2">
                        <button
                          onClick={() => handleRespond(review.id)}
                          className="btn-primary text-sm px-3 py-1.5"
                        >Submit</button>
                        <button
                          onClick={() => { setResponding(null); setResponseText(""); }}
                          className="btn-secondary text-sm px-3 py-1.5"
                        >Cancel</button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-1">
                  {!review.firm_response && !responding && (
                    <button
                      onClick={() => { setResponding(review.id); setResponseText(""); }}
                      className="btn-ghost text-xs gap-1"
                    >
                      <MessageSquare className="w-3.5 h-3.5" /> Respond
                    </button>
                  )}
                  {!review.reported && (
                    <button
                      onClick={() => handleReport(review.id)}
                      className="btn-ghost text-xs text-red-400 gap-1"
                    >
                      <Flag className="w-3.5 h-3.5" /> Report
                    </button>
                  )}
                  {review.reported && (
                    <span className="text-xs text-gray-400 px-2">Reported</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
