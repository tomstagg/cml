"use client";

import { useState } from "react";
import { Plus, Trash2, Loader2 } from "lucide-react";
import { firmPricingApi } from "@/lib/api";
import { getStoredToken } from "@/lib/utils";

type Band = { purchase_price_min: number; purchase_price_max: number | null; fee: number };
type Adjustment = { name: string; amount: number; condition: string };
type Disbursement = { name: string; amount: number; vat_applies: boolean };

const CONDITION_OPTIONS: { value: string; label: string }[] = [
  { value: "tenure==leasehold", label: "Tenure is leasehold" },
  { value: "new_build==true", label: "New build" },
  { value: "help_to_buy_isa==true", label: "Help to Buy ISA" },
  { value: "shared_ownership==true", label: "Shared ownership" },
  { value: "mortgage==true", label: "Mortgage required" },
  { value: "", label: "Always applies" },
];

const STANDARD_BANDS: Band[] = [
  { purchase_price_min: 0, purchase_price_max: 250_000, fee: 950 },
  { purchase_price_min: 250_000, purchase_price_max: 500_000, fee: 1_250 },
  { purchase_price_min: 500_000, purchase_price_max: null, fee: 1_750 },
];

const STANDARD_ADJUSTMENTS: Adjustment[] = [
  { name: "Leasehold supplement", amount: 250, condition: "tenure==leasehold" },
  { name: "New build supplement", amount: 200, condition: "new_build==true" },
  { name: "Help to Buy ISA admin", amount: 75, condition: "help_to_buy_isa==true" },
  { name: "Shared ownership supplement", amount: 250, condition: "shared_ownership==true" },
  { name: "Mortgage handling", amount: 150, condition: "mortgage==true" },
];

const STANDARD_DISBURSEMENTS: Disbursement[] = [
  { name: "Local authority search", amount: 180, vat_applies: true },
  { name: "Drainage & water search", amount: 65, vat_applies: true },
  { name: "Environmental search", amount: 45, vat_applies: true },
  { name: "Bankruptcy search", amount: 6, vat_applies: false },
  { name: "Land Registry priority search", amount: 3, vat_applies: false },
  { name: "Land Registry registration fee", amount: 150, vat_applies: false },
];

const MATTER_TYPE_OPTIONS = [
  { value: "purchase", label: "Purchase" },
  { value: "sale", label: "Sale" },
  { value: "purchase_and_sale", label: "Purchase & sale" },
  { value: "remortgage", label: "Remortgage" },
];

export function PriceCardForm({
  onSaved,
  onCancel,
}: {
  onSaved: (card: unknown) => void;
  onCancel: () => void;
}) {
  const [matterTypes, setMatterTypes] = useState<string[]>([
    "purchase",
    "sale",
    "purchase_and_sale",
    "remortgage",
  ]);
  const [bands, setBands] = useState<Band[]>(STANDARD_BANDS);
  const [adjustments, setAdjustments] = useState<Adjustment[]>(STANDARD_ADJUSTMENTS);
  const [disbursements, setDisbursements] = useState<Disbursement[]>(STANDARD_DISBURSEMENTS);
  const [vatApplies, setVatApplies] = useState(true);
  const [excludedNote, setExcludedNote] = useState(
    "Stamp Duty Land Tax, leasehold notice fees, ground rent apportionment, indemnity policies — see the CML disbursement classification page.",
  );
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
        practice_area: "residential_conveyancing",
        matter_types: matterTypes,
        pricing_model: "band",
        bands,
        adjustments: adjustments.map((a) => ({
          name: a.name,
          amount: a.amount,
          condition: a.condition || null,
        })),
        included_disbursements: disbursements,
        excluded_disbursements_note: excludedNote || null,
        vat_applies_to_fees: vatApplies,
      };

      const card = await firmPricingApi.create(token, {
        practice_area: "residential_conveyancing",
        pricing,
      });
      onSaved(card);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card p-6 space-y-6">
      <h2 className="font-semibold text-gray-900">New Conveyancing Price Card</h2>

      {/* Matter types */}
      <div>
        <label className="label">Matter types covered</label>
        <div className="flex gap-2 flex-wrap">
          {MATTER_TYPE_OPTIONS.map((type) => (
            <button
              key={type.value}
              type="button"
              onClick={() => toggleMatterType(type.value)}
              className={`px-3 py-1.5 rounded-lg border text-sm font-medium transition-colors ${
                matterTypes.includes(type.value)
                  ? "bg-navy text-white border-navy"
                  : "bg-white text-gray-600 border-gray-300"
              }`}
            >
              {type.label}
            </button>
          ))}
        </div>
      </div>

      {/* Bands */}
      <div>
        <label className="label">Fee bands (by purchase price)</label>
        <div className="space-y-2">
          {bands.map((band, i) => (
            <div key={i} className="flex items-center gap-2 flex-wrap">
              <div className="flex items-center gap-1">
                <span className="text-sm text-gray-500">£</span>
                <input
                  type="number"
                  value={band.purchase_price_min}
                  onChange={(e) => {
                    const b = [...bands];
                    b[i].purchase_price_min = Number(e.target.value);
                    setBands(b);
                  }}
                  className="input w-32 text-sm"
                  placeholder="Min"
                />
              </div>
              <span className="text-gray-400">–</span>
              <div className="flex items-center gap-1">
                <span className="text-sm text-gray-500">£</span>
                <input
                  type="number"
                  value={band.purchase_price_max ?? ""}
                  onChange={(e) => {
                    const b = [...bands];
                    b[i].purchase_price_max = e.target.value ? Number(e.target.value) : null;
                    setBands(b);
                  }}
                  className="input w-32 text-sm"
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
            onClick={() =>
              setBands([...bands, { purchase_price_min: 0, purchase_price_max: null, fee: 0 }])
            }
            className="btn-ghost text-sm"
          >
            <Plus className="w-3 h-3" /> Add band
          </button>
        </div>
      </div>

      {/* Adjustments */}
      <div>
        <label className="label">Adjustments (conditional supplements)</label>
        <div className="space-y-2">
          {adjustments.map((adj, i) => (
            <div key={i} className="flex items-center gap-2 flex-wrap">
              <input
                className="input flex-1 min-w-[180px] text-sm"
                value={adj.name}
                onChange={(e) => {
                  const a = [...adjustments];
                  a[i].name = e.target.value;
                  setAdjustments(a);
                }}
                placeholder="Name"
              />
              <select
                className="input text-sm"
                value={adj.condition}
                onChange={(e) => {
                  const a = [...adjustments];
                  a[i].condition = e.target.value;
                  setAdjustments(a);
                }}
              >
                {CONDITION_OPTIONS.map((opt) => (
                  <option key={opt.value || "always"} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
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
            onClick={() =>
              setAdjustments([
                ...adjustments,
                { name: "", amount: 0, condition: "tenure==leasehold" },
              ])
            }
            className="btn-ghost text-sm"
          >
            <Plus className="w-3 h-3" /> Add adjustment
          </button>
        </div>
      </div>

      {/* Disbursements */}
      <div>
        <label className="label">Included disbursements</label>
        <p className="text-xs text-gray-500 mb-2">
          Enter amounts <strong>excluding VAT</strong>; tick the VAT box for items where VAT is
          chargeable.
        </p>
        <div className="space-y-2">
          {disbursements.map((d, i) => (
            <div key={i} className="flex items-center gap-2 flex-wrap">
              <input
                className="input flex-1 min-w-[180px] text-sm"
                value={d.name}
                onChange={(e) => {
                  const ds = [...disbursements];
                  ds[i].name = e.target.value;
                  setDisbursements(ds);
                }}
                placeholder="Name"
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
              <label className="flex items-center gap-1 text-xs text-gray-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={d.vat_applies}
                  onChange={(e) => {
                    const ds = [...disbursements];
                    ds[i].vat_applies = e.target.checked;
                    setDisbursements(ds);
                  }}
                  className="rounded"
                />
                VAT
              </label>
              <button
                onClick={() => setDisbursements(disbursements.filter((_, j) => j !== i))}
                className="btn-ghost text-red-400 p-1"
                type="button"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={() =>
              setDisbursements([...disbursements, { name: "", amount: 0, vat_applies: false }])
            }
            className="btn-ghost text-sm"
          >
            <Plus className="w-3 h-3" /> Add disbursement
          </button>
        </div>
      </div>

      {/* Excluded disbursements note */}
      <div>
        <label className="label">Excluded disbursements (shown to consumer)</label>
        <textarea
          className="input w-full text-sm"
          rows={2}
          value={excludedNote}
          onChange={(e) => setExcludedNote(e.target.value)}
          placeholder="e.g. Stamp Duty Land Tax, leasehold notice fees…"
        />
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
        <button onClick={handleSave} disabled={saving} className="btn-gradient">
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : "Save Price Card"}
        </button>
        <button onClick={onCancel} className="btn-secondary">
          Cancel
        </button>
      </div>
    </div>
  );
}
