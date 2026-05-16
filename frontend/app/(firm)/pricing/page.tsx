"use client";

import { useEffect, useState } from "react";
import { Loader2, Pencil } from "lucide-react";
import { firmPricingApi, type PriceCard } from "@/lib/api";
import { getStoredToken, formatCurrency } from "@/lib/utils";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { PriceCardForm } from "@/components/firm/PriceCardForm";

const PRICE_TYPE_LABEL: Record<PriceCard["price_type"], string> = {
  verified: "Verified by firm",
  estimated: "Estimated (transparency statement)",
  no_data: "No data",
};

const ANCHORS = [150_000, 250_000, 500_000, 750_000, 1_000_000, 1_250_000, 1_500_000] as const;

export default function PricingPage() {
  const router = useRouter();
  const [card, setCard] = useState<PriceCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      router.push("/login");
      return;
    }
    firmPricingApi
      .get(token)
      .then((data) => {
        setCard(data);
        // Open the editor automatically if the firm has no card yet.
        if (data === null) setEditing(true);
      })
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

  if (editing) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-navy mb-6">Fees & Service Offering</h1>
        <PriceCardForm
          initial={card}
          onSaved={(saved) => {
            setCard(saved);
            setEditing(false);
            toast.success("Price card saved");
          }}
          onCancel={() => setEditing(false)}
        />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-navy">Fees & Service Offering</h1>
          <p className="text-gray-500 text-sm mt-1">Your conveyancing price card.</p>
        </div>
        {card && (
          <button onClick={() => setEditing(true)} className="btn-gradient">
            <Pencil className="w-4 h-4" /> Edit price card
          </button>
        )}
      </div>

      {card === null ? (
        <div className="card p-12 text-center text-gray-400">
          <p>No price card yet. Add your conveyancing pricing to appear in search results.</p>
        </div>
      ) : (
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-3">
            <span className="font-semibold text-navy">Residential conveyancing</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-mint/30 text-navy">
              {PRICE_TYPE_LABEL[card.price_type]}
            </span>
          </div>
          <p className="text-xs text-gray-400 mb-4">
            Updated {new Date(card.updated_at).toLocaleDateString("en-GB")}
          </p>

          {card.price_type === "no_data" ? (
            <p className="text-sm text-gray-500">
              No anchor prices recorded — your firm currently won&apos;t appear in search
              results until a price card is published.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-gray-500 border-b border-gray-100">
                    <th className="text-left font-medium pb-2 pr-3">Purchase price</th>
                    <th className="text-right font-medium pb-2 px-2">FH purchase</th>
                    <th className="text-right font-medium pb-2 px-2">FH sale</th>
                    <th className="text-right font-medium pb-2 px-2">LH purchase</th>
                    <th className="text-right font-medium pb-2 px-2">LH sale</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {ANCHORS.map((anchor) => (
                    <tr key={anchor}>
                      <td className="py-1.5 pr-3 text-gray-600">{formatCurrency(anchor)}</td>
                      {(
                        [
                          ["freehold", "purchase"],
                          ["freehold", "sale"],
                          ["leasehold", "purchase"],
                          ["leasehold", "sale"],
                        ] as const
                      ).map(([tenure, txn]) => {
                        const v =
                          card.pricing[tenure]?.[txn]?.[String(anchor)] ??
                          card.pricing[tenure]?.[txn]?.[anchor];
                        return (
                          <td
                            key={`${tenure}-${txn}`}
                            className="py-1.5 px-2 text-right text-navy"
                          >
                            {v != null ? formatCurrency(v) : "—"}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-xs text-gray-400 mt-3">
                VAT (20%) is added to legal fees at quote time. Searches and other disbursements
                are listed in the price card editor.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
