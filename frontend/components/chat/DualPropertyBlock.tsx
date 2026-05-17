"use client";

import { useState } from "react";
import { ArrowRight, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { CURRENCY_MAX, CURRENCY_MIN, currencyOutOfBoundsMessage } from "@/lib/intake";

type TenureOption = { value: string; label: string };

type Side = "purchase" | "sale";

type Block = {
  purchase_tenure_type: string;
  purchase_property_value: number | null;
  sale_tenure_type: string;
  sale_property_value: number | null;
};

type Props = {
  tenureOptions: TenureOption[];
  onSubmit: (block: Omit<Block, "purchase_property_value" | "sale_property_value"> & {
    purchase_property_value: number;
    sale_property_value: number;
  }) => void;
  disabled?: boolean;
};

const EXPLAINER = (
  <>
    Freehold means you own the property and the land outright. Leasehold means you own it under a
    fixed-term lease from the freeholder (common for flats). Your sale or purchase contract will
    say which applies.
  </>
);

function parsePounds(raw: string): number | null {
  const cleaned = raw.replace(/[£,\s]/g, "").trim();
  if (!cleaned) return null;
  const n = Number(cleaned);
  return Number.isFinite(n) && n > 0 ? n : null;
}

export function DualPropertyBlock({ tenureOptions, onSubmit, disabled }: Props) {
  const [purchaseTenure, setPurchaseTenure] = useState("");
  const [purchasePrice, setPurchasePrice] = useState("");
  const [saleTenure, setSaleTenure] = useState("");
  const [salePrice, setSalePrice] = useState("");
  const [showExplainer, setShowExplainer] = useState<Side | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  function handleTenureClick(side: Side, value: string) {
    if (value === "unsure") {
      setShowExplainer(side);
      return;
    }
    if (side === "purchase") setPurchaseTenure(value);
    else setSaleTenure(value);
    setShowExplainer(null);
  }

  function handleContinue() {
    const nextErrors: Record<string, string> = {};
    if (!purchaseTenure || purchaseTenure === "unsure")
      nextErrors.purchase_tenure_type = "Pick freehold or leasehold for the property you're buying.";
    if (!saleTenure || saleTenure === "unsure")
      nextErrors.sale_tenure_type = "Pick freehold or leasehold for the property you're selling.";
    const purchaseValue = parsePounds(purchasePrice);
    const saleValue = parsePounds(salePrice);
    if (!purchaseValue) nextErrors.purchase_property_value = "Enter a purchase price.";
    else if (purchaseValue < CURRENCY_MIN || purchaseValue > CURRENCY_MAX)
      nextErrors.purchase_property_value = currencyOutOfBoundsMessage("purchase");
    if (!saleValue) nextErrors.sale_property_value = "Enter a sale price.";
    else if (saleValue < CURRENCY_MIN || saleValue > CURRENCY_MAX)
      nextErrors.sale_property_value = currencyOutOfBoundsMessage("sale");

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    onSubmit({
      purchase_tenure_type: purchaseTenure,
      purchase_property_value: purchaseValue as number,
      sale_tenure_type: saleTenure,
      sale_property_value: saleValue as number,
    });
  }

  return (
    <div className="space-y-4 max-w-2xl">
      <div className="grid sm:grid-cols-2 gap-4">
        <SideBlock
          title="Buying"
          tenureOptions={tenureOptions}
          tenureValue={purchaseTenure}
          onTenureClick={(v) => handleTenureClick("purchase", v)}
          priceValue={purchasePrice}
          onPriceChange={setPurchasePrice}
          tenureError={errors.purchase_tenure_type}
          priceError={errors.purchase_property_value}
          disabled={disabled}
        />
        <SideBlock
          title="Selling"
          tenureOptions={tenureOptions}
          tenureValue={saleTenure}
          onTenureClick={(v) => handleTenureClick("sale", v)}
          priceValue={salePrice}
          onPriceChange={setSalePrice}
          tenureError={errors.sale_tenure_type}
          priceError={errors.sale_property_value}
          disabled={disabled}
        />
      </div>

      {showExplainer && (
        <div className="rounded-lg border border-purple/20 bg-purple/5 p-3 text-xs text-ink-muted flex gap-2">
          <Info className="w-4 h-4 text-purple flex-shrink-0 mt-0.5" />
          <p>{EXPLAINER}</p>
        </div>
      )}

      <button
        type="button"
        onClick={handleContinue}
        disabled={disabled}
        className="btn-primary px-4 py-2"
      >
        Continue
        <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
}

function SideBlock({
  title,
  tenureOptions,
  tenureValue,
  onTenureClick,
  priceValue,
  onPriceChange,
  tenureError,
  priceError,
  disabled,
}: {
  title: string;
  tenureOptions: TenureOption[];
  tenureValue: string;
  onTenureClick: (v: string) => void;
  priceValue: string;
  onPriceChange: (v: string) => void;
  tenureError?: string;
  priceError?: string;
  disabled?: boolean;
}) {
  return (
    <div className="rounded-lg border border-navy/10 bg-white p-4">
      <p className="font-semibold text-navy mb-3">{title}</p>
      <label className="label text-xs">Tenure</label>
      <div className="flex flex-wrap gap-2 mb-3">
        {tenureOptions.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onTenureClick(opt.value)}
            disabled={disabled}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
              tenureValue === opt.value
                ? "border-navy bg-navy text-white"
                : "border-navy/30 bg-white text-navy hover:border-navy",
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>
      {tenureError && <p className="text-red-500 text-xs mb-2">{tenureError}</p>}

      <label className="label text-xs">Property value</label>
      <input
        type="text"
        inputMode="decimal"
        value={priceValue}
        onChange={(e) => onPriceChange(e.target.value)}
        placeholder="£275,000"
        disabled={disabled}
        className="input w-full"
      />
      {priceError && <p className="text-red-500 text-xs mt-1">{priceError}</p>}
    </div>
  );
}
