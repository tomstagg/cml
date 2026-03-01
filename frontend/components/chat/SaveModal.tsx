"use client";

import { useState } from "react";
import { X, Loader2, CheckCircle } from "lucide-react";
import { toast } from "sonner";
import { sessionsApi } from "@/lib/api";

type Props = {
  sessionId: string;
  onClose: () => void;
};

export function SaveModal({ sessionId, onClose }: Props) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSave() {
    if (!email.trim()) return;
    setLoading(true);
    try {
      await sessionsApi.save(sessionId, email.trim());
      setDone(true);
    } catch {
      toast.error("Failed to save. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Save for later</h2>
          <button onClick={onClose} className="btn-ghost p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {done ? (
          <div className="text-center py-6">
            <CheckCircle className="w-12 h-12 text-brand-600 mx-auto mb-3" />
            <p className="font-medium text-gray-900 mb-1">Email sent!</p>
            <p className="text-gray-500 text-sm">
              Check your inbox for a link to resume your comparison.
            </p>
            <button onClick={onClose} className="btn-primary mt-4">
              Continue
            </button>
          </div>
        ) : (
          <>
            <p className="text-gray-600 text-sm mb-4">
              Enter your email and we'll send you a link to continue your comparison later.
            </p>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="input mb-4"
              onKeyDown={(e) => e.key === "Enter" && handleSave()}
              autoFocus
            />
            <button
              onClick={handleSave}
              disabled={loading || !email.trim()}
              className="btn-primary w-full"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Send Link"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
