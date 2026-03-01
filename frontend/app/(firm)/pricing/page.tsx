"use client";

import { useEffect, useState } from "react";
import { Loader2, Plus, Trash2, Eye } from "lucide-react";
import { firmPricingApi } from "@/lib/api";
import { getStoredToken, formatCurrency } from "@/lib/utils";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { PriceCardForm } from "@/components/firm/PriceCardForm";

type PriceCard = {
  id: string;
  practice_area: string;
  pricing: {
    pricing_model: string;
    bands: { estate_value_min: number; estate_value_max: number | null; fee: number }[];
    matter_types: string[];
    vat_applies_to_fees: boolean;
  };
  active: boolean;
  updated_at: string;
};

export default function PricingPage() {
  const router = useRouter();
  const [cards, setCards] = useState<PriceCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) { router.push("/firm/login"); return; }
    firmPricingApi.list(token)
      .then((data) => setCards(data as PriceCard[]))
      .catch(() => router.push("/firm/login"))
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(cardId: string) {
    const token = getStoredToken();
    if (!token) return;
    if (!confirm("Deactivate this price card?")) return;
    await firmPricingApi.delete(token, cardId);
    setCards((prev) => prev.filter((c) => c.id !== cardId));
    toast.success("Price card deactivated");
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
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Pricing</h1>
          <p className="text-gray-500 text-sm mt-1">Manage your probate price cards.</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary">
          <Plus className="w-4 h-4" /> Add Price Card
        </button>
      </div>

      {showForm && (
        <div className="mb-6">
          <PriceCardForm
            onSaved={(card) => {
              setCards((prev) => [card as PriceCard, ...prev.filter((c) => c.id !== (card as PriceCard).id)]);
              setShowForm(false);
              toast.success("Price card saved!");
            }}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}

      {cards.length === 0 ? (
        <div className="card p-12 text-center text-gray-400">
          <p>No price cards yet. Add your probate pricing to appear in search results.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {cards.map((card) => (
            <div key={card.id} className="card p-5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-gray-900 capitalize">{card.practice_area}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${card.active ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                      {card.active ? "Active" : "Inactive"}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">
                    {card.pricing.pricing_model} pricing ·{" "}
                    {card.pricing.matter_types.join(", ").replace("_", " ")} ·{" "}
                    {card.pricing.bands.length} band{card.pricing.bands.length !== 1 ? "s" : ""}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Updated {new Date(card.updated_at).toLocaleDateString("en-GB")}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDelete(card.id)}
                    className="btn-ghost text-red-500 hover:text-red-700 p-2"
                    title="Deactivate"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Band preview */}
              {card.pricing.bands.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-xs text-gray-400">
                        <th className="text-left font-medium pb-1">Estate value band</th>
                        <th className="text-right font-medium pb-1">Legal fee</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {card.pricing.bands.map((band, i) => (
                        <tr key={i}>
                          <td className="py-1.5 text-gray-600">
                            {formatCurrency(band.estate_value_min)} –{" "}
                            {band.estate_value_max ? formatCurrency(band.estate_value_max) : "above"}
                          </td>
                          <td className="py-1.5 text-right font-medium text-gray-900">
                            {formatCurrency(band.fee)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {card.pricing.vat_applies_to_fees && (
                    <p className="text-xs text-gray-400 mt-2">VAT (20%) applies to legal fees</p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
