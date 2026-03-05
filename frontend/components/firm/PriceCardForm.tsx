"use client";

import { useState } from "react";
import { Plus, Trash2, Loader2 } from "lucide-react";
import { firmPricingApi } from "@/lib/api";
import { getStoredToken } from "@/lib/utils";

type Band = { estate_value_min: number; estate_value_max: number | null; fee: number };
type Adjustment = { name: string; amount: number; condition: string | null };
type Disbursement = { name: string; amount: number; estimated: boolean };

const STANDARD_DISBURSEMENTS: Disbursement[] = [
  { name: "Probate Registry application fee", amount: 273, estimated: false },
  { name: "Office copy entries (Land Registry)", amount: 12, estimated: true },
  { name: "Bankruptcy search (per beneficiary)", amount: 2, estimated: true },
];

const STANDARD_ADJUSTMENTS: Adjustment[] = [
  { name: "Taxable estate (IHT400 required)", amount: 500, condition: "iht400" },
  { name: "Overseas assets", amount: 750, condition: "overseas_assets" },
  { name: "Complex investment portfolio", amount: 500, condition: "complex_investments" },
];

export function PriceCardForm({
  onSaved,
  onCancel,
}: {
  onSaved: (card: unknown) => void;
  onCancel: () => void;
}) {
  const [pricingModel, setPricingModel] = useState<"fixed" | "band" | "percentage">("band");
  const [matterTypes, setMatterTypes] = useState<string[]>(["full_administration"]);
  const [bands, setBands] = useState<Band[]>([
    { estate_value_min: 0, estate_value_max: 325000, fee: 1500 },
    { estate_value_min: 325001, estate_value_max: 650000, fee: 2500 },
    { estate_value_min: 650001, estate_value_max: null, fee: 3500 },
  ]);
  const [adjustments, setAdjustments] = useState<Adjustment[]>(STANDARD_ADJUSTMENTS);
  const [disbursements, setDisbursements] = useState<Disbursement[]>(STANDARD_DISBURSEMENTS);
  const [vatApplies, setVatApplies] = useState(true);
  const [saving, setSaving] = useState(false);

  function toggleMatterType(type: string) {
    setMatterTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type],
    );
  }

  async function handleSave() {
    const token = getStoredToken();
    if (!token) return;

    setSaving(true);
    try {
      const pricing = {
        practice_area: "probate",
        matter_types: matterTypes,
        pricing_model: pricingModel,
        bands,
        adjustments,
        disbursements,
        vat_applies_to_fees: vatApplies,
      };

      const card = await firmPricingApi.create(token, { practice_area: "probate", pricing });
      onSaved(card);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card p-6 space-y-6">
      <h2 className="font-semibold text-gray-900">New Probate Price Card</h2>

      {/* Matter types */}
      <div>
        <label className="label">Matter types covered</label>
        <div className="flex gap-3 flex-wrap">
          {[
            { value: "grant_only", label: "Grant only" },
            { value: "full_administration", label: "Full administration" },
          ].map((type) => (
            <button
              key={type.value}
              type="button"
              onClick={() => toggleMatterType(type.value)}
              className={`px-3 py-1.5 rounded-lg border text-sm font-medium transition-colors ${
                matterTypes.includes(type.value)
                  ? "bg-brand-600 text-white border-brand-600"
                  : "bg-white text-gray-600 border-gray-300"
              }`}
            >
              {type.label}
            </button>
          ))}
        </div>
      </div>

      {/* Pricing model */}
      <div>
        <label className="label">Pricing model</label>
        <div className="flex gap-3">
          {["fixed", "band", "percentage"].map((model) => (
            <button
              key={model}
              type="button"
              onClick={() => setPricingModel(model as typeof pricingModel)}
              className={`px-3 py-1.5 rounded-lg border text-sm font-medium capitalize transition-colors ${
                pricingModel === model
                  ? "bg-brand-600 text-white border-brand-600"
                  : "bg-white text-gray-600 border-gray-300"
              }`}
            >
              {model}
            </button>
          ))}
        </div>
      </div>

      {/* Bands */}
      {pricingModel === "band" && (
        <div>
          <label className="label">Fee bands (by estate value)</label>
          <div className="space-y-2">
            {bands.map((band, i) => (
              <div key={i} className="flex items-center gap-2 flex-wrap">
                <div className="flex items-center gap-1">
                  <span className="text-sm text-gray-500">£</span>
                  <input
                    type="number"
                    value={band.estate_value_min}
                    onChange={(e) => {
                      const b = [...bands];
                      b[i].estate_value_min = Number(e.target.value);
                      setBands(b);
                    }}
                    className="input w-28 text-sm"
                    placeholder="Min"
                  />
                </div>
                <span className="text-gray-400">–</span>
                <div className="flex items-center gap-1">
                  <span className="text-sm text-gray-500">£</span>
                  <input
                    type="number"
                    value={band.estate_value_max ?? ""}
                    onChange={(e) => {
                      const b = [...bands];
                      b[i].estate_value_max = e.target.value ? Number(e.target.value) : null;
                      setBands(b);
                    }}
                    className="input w-28 text-sm"
                    placeholder="Max (blank = above)"
                  />
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-sm text-gray-500">Fee £</span>
                  <input
                    type="number"
                    value={band.fee}
                    onChange={(e) => {
                      const b = [...bands];
                      b[i].fee = Number(e.target.value);
                      setBands(b);
                    }}
                    className="input w-24 text-sm"
                  />
                </div>
                <button
                  onClick={() => setBands(bands.filter((_, j) => j !== i))}
                  className="btn-ghost text-red-400 p-1"
                  type="button"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
            <button
              type="button"
              onClick={() => setBands([...bands, { estate_value_min: 0, estate_value_max: null, fee: 0 }])}
              className="btn-ghost text-sm"
            >
              <Plus className="w-3 h-3" /> Add band
            </button>
          </div>
        </div>
      )}

      {/* Adjustments */}
      <div>
        <label className="label">Adjustments (complexity extras)</label>
        <div className="space-y-2">
          {adjustments.map((adj, i) => (
            <div key={i} className="flex items-center gap-2">
              <input
                className="input flex-1 text-sm"
                value={adj.name}
                onChange={(e) => {
                  const a = [...adjustments];
                  a[i].name = e.target.value;
                  setAdjustments(a);
                }}
                placeholder="Adjustment name"
              />
              <span className="text-sm text-gray-500">£</span>
              <input
                type="number"
                className="input w-24 text-sm"
                value={adj.amount}
                onChange={(e) => {
                  const a = [...adjustments];
                  a[i].amount = Number(e.target.value);
                  setAdjustments(a);
                }}
              />
              <button
                onClick={() => setAdjustments(adjustments.filter((_, j) => j !== i))}
                className="btn-ghost text-red-400 p-1"
                type="button"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={() => setAdjustments([...adjustments, { name: "", amount: 0, condition: null }])}
            className="btn-ghost text-sm"
          >
            <Plus className="w-3 h-3" /> Add adjustment
          </button>
        </div>
      </div>

      {/* Disbursements */}
      <div>
        <label className="label">Disbursements</label>
        <div className="space-y-2">
          {disbursements.map((d, i) => (
            <div key={i} className="flex items-center gap-2">
              <input
                className="input flex-1 text-sm"
                value={d.name}
                onChange={(e) => {
                  const ds = [...disbursements];
                  ds[i].name = e.target.value;
                  setDisbursements(ds);
                }}
              />
              <span className="text-sm text-gray-500">£</span>
              <input
                type="number"
                className="input w-24 text-sm"
                value={d.amount}
                onChange={(e) => {
                  const ds = [...disbursements];
                  ds[i].amount = Number(e.target.value);
                  setDisbursements(ds);
                }}
              />
              <button
                onClick={() => setDisbursements(disbursements.filter((_, j) => j !== i))}
                className="btn-ghost text-red-400 p-1"
                type="button"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* VAT */}
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={vatApplies}
          onChange={(e) => setVatApplies(e.target.checked)}
          className="rounded"
        />
        <span className="text-sm text-gray-700">VAT (20%) applies to legal fees</span>
      </label>

      {/* Actions */}
      <div className="flex gap-3 pt-2 border-t border-gray-100">
        <button onClick={handleSave} disabled={saving} className="btn-primary">
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : "Save Price Card"}
        </button>
        <button onClick={onCancel} className="btn-secondary">Cancel</button>
      </div>
    </div>
  );
}
