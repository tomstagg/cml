"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getConsent, setConsent } from "@/lib/consent";

export function CookieConsent() {
  const [decided, setDecided] = useState(true); // hide until we read storage

  useEffect(() => {
    setDecided(getConsent() !== null);
  }, []);

  if (decided) return null;

  const decide = (state: "accepted" | "rejected") => {
    setConsent(state);
    setDecided(true);
  };

  return (
    <div
      role="dialog"
      aria-label="Cookie preferences"
      className="fixed inset-x-0 bottom-0 z-50 border-t border-navy/20 bg-navy/95 text-white backdrop-blur"
    >
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:py-3">
        <p className="text-sm leading-snug">
          We use cookies for analytics and to measure the performance of our marketing.
          See our{" "}
          <Link href="/privacy" className="underline hover:text-teal">
            privacy policy
          </Link>
          .
        </p>
        <div className="flex shrink-0 gap-2">
          <button
            type="button"
            onClick={() => decide("rejected")}
            className="rounded-full border border-white/40 px-4 py-2 text-sm font-medium hover:bg-white/10"
          >
            Reject
          </button>
          <button
            type="button"
            onClick={() => decide("accepted")}
            className="rounded-full bg-gradient-to-r from-purple to-teal px-4 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            Accept
          </button>
        </div>
      </div>
    </div>
  );
}
