"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { firmPricingApi, type PriceCard, type PriceCardData } from "@/lib/api";
import { getStoredToken, formatCurrency } from "@/lib/utils";

const ANCHORS: { value: number; label: string }[] = [
  { value: 150_000, label: "£150k" },
  { value: 250_000, label: "£250k" },
  { value: 500_000, label: "£500k" },
  { value: 750_000, label: "£750k" },
  { value: 1_000_000, label: "£1m" },
  { value: 1_250_000, label: "£1.25m" },
  { value: 1_500_000, label: "£1.5m" },
];

const MATTERS: { key: "fhp" | "fhs" | "lhp" | "lhs"; label: string; tenure: "freehold" | "leasehold"; txn: "purchase" | "sale" }[] = [
  { key: "fhp", label: "Freehold purchase", tenure: "freehold", txn: "purchase" },
  { key: "fhs", label: "Freehold sale", tenure: "freehold", txn: "sale" },
  { key: "lhp", label: "Leasehold purchase", tenure: "leasehold", txn: "purchase" },
  { key: "lhs", label: "Leasehold sale", tenure: "leasehold", txn: "sale" },
];

const STANDARD_MODIFIERS = [
  "Purchase - New build (freehold)",
  "Purchase - New lease (leasehold)",
  "Purchase - Acting for lender",
  "Purchase - Shared ownership/Help to Buy",
  "Purchase - Gifted deposit",
  "Purchase - Unregistered title",
  "Sale - Unregistered title",
  "Sale - Additional mortgage redemption",
];

const STANDARD_ADDITIONAL_COSTS = [
  "Additional - ID verification",
  "Additional - onboarding fee",
  "Additional - transfer admin fee",
  "SDLT admin fee",
  "Leasehold admin fee",
];

const SEARCHES_DISBURSEMENT_NAME = "Disb - searches (CML standard pack)";

type AmountMap = Record<string, number | null>;

function emptyAnchorMap(): AmountMap {
  return Object.fromEntries(ANCHORS.map((a) => [a.value, null])) as AmountMap;
}

function emptyNamedAmounts(names: string[]): Record<string, number> {
  return Object.fromEntries(names.map((n) => [n, 0]));
}

export function PriceCardForm({
  initial,
  onSaved,
  onCancel,
}: {
  initial?: PriceCard | null;
  onSaved: (card: PriceCard) => void;
  onCancel: () => void;
}) {
  const [anchorPrices, setAnchorPrices] = useState<Record<typeof MATTERS[number]["key"], AmountMap>>(() => {
    const base = {
      fhp: emptyAnchorMap(),
      fhs: emptyAnchorMap(),
      lhp: emptyAnchorMap(),
      lhs: emptyAnchorMap(),
    };
    if (!initial) return base;
    for (const m of MATTERS) {
      const src = (initial.pricing[m.tenure]?.[m.txn] ?? {}) as Record<string, number | null>;
      for (const a of ANCHORS) {
        base[m.key][a.value] = src[String(a.value)] ?? src[a.value] ?? null;
      }
    }
    return base;
  });

  const [modifiers, setModifiers] = useState<Record<string, number>>(() => {
    const base = emptyNamedAmounts(STANDARD_MODIFIERS);
    initial?.pricing.modifiers?.forEach((m) => {
      if (m.name in base) base[m.name] = m.amount;
    });
    return base;
  });

  const [additionalCosts, setAdditionalCosts] = useState<Record<string, number>>(() => {
    const base = emptyNamedAmounts(STANDARD_ADDITIONAL_COSTS);
    initial?.pricing.additional_costs?.forEach((m) => {
      if (m.name in base) base[m.name] = m.amount;
    });
    return base;
  });

  const [searches, setSearches] = useState<number>(() => {
    const d = initial?.pricing.disbursements?.[0];
    return d?.amount ?? 350;
  });

  const [saving, setSaving] = useState(false);

  function setAnchor(matter: typeof MATTERS[number]["key"], anchor: number, value: string) {
    const parsed = value.trim() === "" ? null : Number(value);
    setAnchorPrices((prev) => ({
      ...prev,
      [matter]: { ...prev[matter], [anchor]: parsed },
    }));
  }

  function buildPricing(): PriceCardData {
    const matterMap = (key: typeof MATTERS[number]["key"]) =>
      Object.fromEntries(
        ANCHORS.map((a) => [String(a.value), anchorPrices[key][a.value]]),
      ) as Record<string, number | null>;
    return {
      freehold: {
        purchase: matterMap("fhp"),
        sale: matterMap("fhs"),
      },
      leasehold: {
        purchase: matterMap("lhp"),
        sale: matterMap("lhs"),
      },
      modifiers: Object.entries(modifiers).map(([name, amount]) => ({ name, amount })),
      additional_costs: Object.entries(additionalCosts).map(([name, amount]) => ({ name, amount })),
      disbursements: [{ name: SEARCHES_DISBURSEMENT_NAME, amount: searches }],
    };
  }

  async function handleSave() {
    const token = getStoredToken();
    if (!token) return;
    setSaving(true);
    try {
      const card = await firmPricingApi.upsert(token, buildPricing());
      onSaved(card);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card p-6 space-y-8">
      <header>
        <h2 className="font-semibold text-navy text-lg">Conveyancing price card</h2>
        <p className="text-sm text-gray-500 mt-1">
          Enter your legal fees at each purchase-price anchor for the four matter types CML
          compares. Leave a cell blank if you don&apos;t offer that combination.
        </p>
      </header>

      {/* Anchor-price matrix */}
      <section>
        <h3 className="label">Legal fees by matter and purchase price</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-500 border-b border-gray-100">
                <th className="text-left font-medium pb-2 pr-3">Purchase price</th>
                {MATTERS.map((m) => (
                  <th key={m.key} className="text-right font-medium pb-2 px-2">
                    {m.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {ANCHORS.map((a) => (
                <tr key={a.value}>
                  <td className="py-2 pr-3 text-gray-600">{a.label}</td>
                  {MATTERS.map((m) => (
                    <td key={m.key} className="py-1 px-1">
                      <div className="flex items-center justify-end gap-1">
                        <span className="text-xs text-gray-400">£</span>
                        <input
                          type="number"
                          inputMode="numeric"
                          value={anchorPrices[m.key][a.value] ?? ""}
                          onChange={(e) => setAnchor(m.key, a.value, e.target.value)}
                          className="input w-24 text-sm text-right"
                          placeholder="—"
                        />
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Modifiers */}
      <section>
        <h3 className="label">Modifiers (transaction-specific supplements)</h3>
        <p className="text-xs text-gray-500 mb-2">
          Enter £0 if the modifier doesn&apos;t apply.
        </p>
        <div className="grid sm:grid-cols-2 gap-2">
          {STANDARD_MODIFIERS.map((name) => (
            <label key={name} className="flex items-center gap-2">
              <span className="text-sm text-gray-700 flex-1">{name}</span>
              <span className="text-xs text-gray-400">£</span>
              <input
                type="number"
                inputMode="numeric"
                className="input w-24 text-sm text-right"
                value={modifiers[name]}
                onChange={(e) =>
                  setModifiers((prev) => ({ ...prev, [name]: Number(e.target.value) }))
                }
              />
            </label>
          ))}
        </div>
      </section>

      {/* Additional costs */}
      <section>
        <h3 className="label">Additional costs (not disbursements)</h3>
        <div className="grid sm:grid-cols-2 gap-2">
          {STANDARD_ADDITIONAL_COSTS.map((name) => (
            <label key={name} className="flex items-center gap-2">
              <span className="text-sm text-gray-700 flex-1">{name}</span>
              <span className="text-xs text-gray-400">£</span>
              <input
                type="number"
                inputMode="numeric"
                className="input w-24 text-sm text-right"
                value={additionalCosts[name]}
                onChange={(e) =>
                  setAdditionalCosts((prev) => ({ ...prev, [name]: Number(e.target.value) }))
                }
              />
            </label>
          ))}
        </div>
      </section>

      {/* Disbursements */}
      <section>
        <h3 className="label">Disbursements</h3>
        <p className="text-xs text-gray-500 mb-2">
          Searches are held constant across firms for comparability. Other disbursements (Stamp
          Duty, Land Registry fees, leasehold notice fees, indemnity policies) are confirmed
          per-matter and excluded from the headline quote.
        </p>
        <label className="flex items-center gap-2 max-w-sm">
          <span className="text-sm text-gray-700 flex-1">{SEARCHES_DISBURSEMENT_NAME}</span>
          <span className="text-xs text-gray-400">£</span>
          <input
            type="number"
            inputMode="numeric"
            className="input w-24 text-sm text-right"
            value={searches}
            onChange={(e) => setSearches(Number(e.target.value))}
          />
        </label>
        <p className="text-xs text-gray-400 mt-2">
          Total preview at £{ANCHORS[1].value.toLocaleString()} purchase, freehold:{" "}
          <strong className="text-navy">
            {anchorPrices.fhp[ANCHORS[1].value] != null
              ? formatCurrency((anchorPrices.fhp[ANCHORS[1].value] ?? 0) * 1.2 + searches)
              : "—"}
          </strong>{" "}
          (fee + 20% VAT + searches)
        </p>
      </section>

      {/* Actions */}
      <div className="flex gap-3 pt-4 border-t border-gray-100">
        <button onClick={handleSave} disabled={saving} className="btn-gradient">
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : "Save price card"}
        </button>
        <button onClick={onCancel} className="btn-secondary">
          Cancel
        </button>
      </div>
    </div>
  );
}
