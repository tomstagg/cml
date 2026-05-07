"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { firmDashboardApi } from "@/lib/api";
import { cn, getStoredToken } from "@/lib/utils";

type Stats = {
  new_appointments_30d: number;
  video_call_requests_30d: number;
  appearances_in_results_30d: number;
  new_reviews_30d: number;
};

type Card = {
  label: string;
  count: number;
  bg: string;
  href: string | null;
};

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      router.push("/login");
      return;
    }
    firmDashboardApi
      .getStats(token)
      .then((data) => setStats(data as Stats))
      .catch(() => router.push("/login"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="w-8 h-8 text-navy animate-spin" />
      </div>
    );
  }

  if (!stats) return null;

  const cards: Card[] = [
    {
      label: "New appointments",
      count: stats.new_appointments_30d,
      bg: "bg-teal",
      href: null,
    },
    {
      label: "Video call requests",
      count: stats.video_call_requests_30d,
      bg: "bg-white border border-gray-200",
      href: null,
    },
    {
      label: "Appearances in results",
      count: stats.appearances_in_results_30d,
      bg: "bg-purple/20",
      href: null,
    },
    {
      label: "New reviews",
      count: stats.new_reviews_30d,
      bg: "bg-mint",
      href: "/reviews",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
      {cards.map((card) => (
        <article
          key={card.label}
          className={cn("rounded-2xl p-8 text-center", card.bg)}
        >
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-navy text-white text-xl font-bold mb-4">
            {card.count}
          </div>
          <h3 className="text-navy text-lg font-semibold">{card.label}</h3>
          <p className="text-navy/70 text-sm mt-1 mb-4">In the last 30 days</p>
          {card.href ? (
            <Link
              href={card.href}
              className="text-navy font-semibold underline-offset-4 hover:underline"
            >
              View
            </Link>
          ) : (
            <span className="text-navy/40 font-semibold cursor-not-allowed">View</span>
          )}
        </article>
      ))}
    </div>
  );
}
