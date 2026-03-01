"use client";

import { useEffect, useState } from "react";
import { BarChart2, Calendar, MessageSquare, Star } from "lucide-react";
import { firmDashboardApi } from "@/lib/api";
import { getStoredToken, formatCurrency, formatRating } from "@/lib/utils";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

type Stats = {
  total_appearances: number;
  total_appointments: number;
  total_callbacks: number;
  aggregate_rating: number | null;
  aggregate_review_count: number | null;
  recent_appointments: {
    id: string;
    type: string;
    status: string;
    client_name: string;
    quoted_price: number | null;
    created_at: string;
  }[];
};

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) { router.push("/firm/login"); return; }

    firmDashboardApi
      .getStats(token)
      .then((data) => setStats(data as Stats))
      .catch(() => router.push("/firm/login"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-brand-600 animate-spin" />
      </div>
    );
  }

  if (!stats) return null;

  const statCards = [
    { label: "Appointments", value: stats.total_appointments, icon: Calendar, color: "brand" },
    { label: "Callbacks", value: stats.total_callbacks, icon: MessageSquare, color: "blue" },
    { label: "Your Rating", value: stats.aggregate_rating ? `${formatRating(stats.aggregate_rating)} / 5` : "No reviews", icon: Star, color: "amber" },
    { label: "Reviews", value: stats.aggregate_review_count ?? 0, icon: BarChart2, color: "purple" },
  ];

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((s) => (
          <div key={s.label} className="card p-5">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-9 h-9 rounded-lg bg-brand-50 flex items-center justify-center">
                <s.icon className="w-5 h-5 text-brand-600" />
              </div>
              <span className="text-sm text-gray-500">{s.label}</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Recent appointments */}
      <div className="card">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Recent Activity</h2>
        </div>
        {stats.recent_appointments.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            No appointments yet. Make sure your price card is active!
          </div>
        ) : (
          <div className="divide-y divide-gray-50">
            {stats.recent_appointments.map((a) => (
              <div key={a.id} className="px-5 py-4 flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">{a.client_name}</p>
                  <p className="text-sm text-gray-500">
                    {a.type === "appoint" ? "Appointment" : "Callback"} ·{" "}
                    {new Date(a.created_at).toLocaleDateString("en-GB")}
                  </p>
                </div>
                <div className="text-right">
                  {a.quoted_price && (
                    <p className="font-medium text-gray-900">{formatCurrency(a.quoted_price)}</p>
                  )}
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    a.status === "pending" ? "bg-amber-50 text-amber-700" :
                    a.status === "confirmed" ? "bg-green-50 text-green-700" :
                    "bg-gray-50 text-gray-600"
                  }`}>
                    {a.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
