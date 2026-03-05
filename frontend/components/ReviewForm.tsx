"use client";

import { useEffect, useState } from "react";
import { Loader2, Star, CheckCircle } from "lucide-react";
import { toast } from "sonner";
import { reviewsApi } from "@/lib/api";

type Props = { token: string };

export function ReviewForm({ token }: Props) {
  const [invitation, setInvitation] = useState<{ firm_name: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [text, setText] = useState("");
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    reviewsApi
      .getInvitation(token)
      .then((data) => setInvitation(data as { firm_name: string }))
      .catch((err) => setError(err.detail || "This review link is invalid or has expired."))
      .finally(() => setLoading(false));
  }, [token]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (rating === 0) { toast.error("Please select a star rating"); return; }
    if (text.length < 10) { toast.error("Review must be at least 10 characters"); return; }

    setSubmitting(true);
    try {
      await reviewsApi.submit({ token, rating, text, reviewer_name: name || undefined });
      setDone(true);
    } catch {
      toast.error("Failed to submit review. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 text-brand-600 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center max-w-sm">
          <p className="text-gray-500">{error}</p>
        </div>
      </div>
    );
  }

  if (done) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <CheckCircle className="w-16 h-16 text-brand-600 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Thank you!</h1>
          <p className="text-gray-500">Your review helps others find great solicitors.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 p-4">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 w-full max-w-lg p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          How was {invitation?.firm_name}?
        </h1>
        <p className="text-gray-500 mb-6">
          Your honest review helps others choose the right solicitor.
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Star rating */}
          <div>
            <label className="label">Rating *</label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setRating(star)}
                  onMouseEnter={() => setHoverRating(star)}
                  onMouseLeave={() => setHoverRating(0)}
                  className="p-1 transition-transform hover:scale-110"
                >
                  <Star
                    className={`w-8 h-8 ${
                      star <= (hoverRating || rating)
                        ? "text-amber-400 fill-amber-400"
                        : "text-gray-200"
                    }`}
                  />
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="label">Your review *</label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="input min-h-[120px] resize-none"
              placeholder="Tell us about your experience (min. 10 characters)"
              maxLength={2000}
            />
            <p className="text-xs text-gray-400 mt-1">{text.length} / 2000</p>
          </div>

          <div>
            <label className="label">Your name (optional)</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input"
              placeholder="e.g. Sarah T. (or leave blank for 'Anonymous')"
              maxLength={100}
            />
          </div>

          <button type="submit" disabled={submitting} className="btn-primary w-full">
            {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Submit Review"}
          </button>
        </form>
      </div>
    </div>
  );
}
