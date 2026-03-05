"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, ExternalLink, MapPin, Star } from "lucide-react";
import { cn, formatCurrency, getAuthStatusColor, getAuthStatusLabel } from "@/lib/utils";

type QuoteBreakdown = {
  base_fee: number;
  adjustments: { name: string; amount: number }[];
  fees_subtotal: number;
  vat: number;
  disbursements: { name: string; amount: number; estimated: boolean }[];
  disbursements_total: number;
  total: number;
  currency: string;
  pricing_model: string;
};

type FirmResult = {
  rank: number;
  org_id: string;
  name: string;
  sra_number: string;
  auth_status: string;
  enrolled: boolean;
  website_url: string | null;
  aggregate_rating: number | null;
  aggregate_review_count: number | null;
  postcode: string | null;
  city: string | null;
  distance_km: number | null;
  quote: QuoteBreakdown | null;
  score: number;
};

type Props = {
  firm: FirmResult;
  onAppoint: () => void;
  onCallback: () => void;
};

export function FirmCard({ firm, onAppoint, onCallback }: Props) {
  const [quoteExpanded, setQuoteExpanded] = useState(false);

  const isEnrolled = firm.enrolled;
  const isTopFive = firm.rank <= 5;

  return (
    <div
      className={cn(
        "card p-5 transition-all",
        !isEnrolled && "opacity-60",
        isEnrolled && isTopFive && "border-brand-200 shadow-sm",
      )}
    >
      <div className="flex flex-col sm:flex-row sm:items-start gap-4">
        {/* Rank badge */}
        <div
          className={cn(
            "flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold",
            isEnrolled && isTopFive
              ? "bg-brand-600 text-white"
              : "bg-gray-100 text-gray-500",
          )}
        >
          {firm.rank}
        </div>

        {/* Firm info */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <h3 className="text-base font-semibold text-gray-900 truncate">{firm.name}</h3>
            <span className={cn("text-xs px-2 py-0.5 rounded-full border font-medium", getAuthStatusColor(firm.auth_status))}>
              {getAuthStatusLabel(firm.auth_status)}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500">
            {firm.aggregate_rating && (
              <span className="flex items-center gap-1">
                <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                {firm.aggregate_rating.toFixed(1)}
                {firm.aggregate_review_count && (
                  <span className="text-gray-400">({firm.aggregate_review_count})</span>
                )}
              </span>
            )}
            {(firm.city || firm.postcode) && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5" />
                {firm.city || firm.postcode}
                {firm.distance_km !== null && ` · ${firm.distance_km} km`}
              </span>
            )}
            {firm.website_url && (
              <a
                href={firm.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-brand-600 hover:underline"
              >
                Website <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>

          {!isEnrolled && (
            <p className="mt-2 text-xs text-gray-400 italic">
              Not enrolled — contact this firm directly via their website.
            </p>
          )}
        </div>

        {/* Quote + CTA */}
        <div className="flex-shrink-0 text-right">
          {firm.quote && (
            <div className="mb-3">
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(firm.quote.total)}
              </p>
              <p className="text-xs text-gray-400">total estimated cost</p>
              <button
                onClick={() => setQuoteExpanded(!quoteExpanded)}
                className="text-xs text-brand-600 hover:underline flex items-center gap-0.5 ml-auto mt-1"
              >
                Breakdown {quoteExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            </div>
          )}

          {isEnrolled && isTopFive && (
            <div className="flex flex-col gap-2">
              <button onClick={onAppoint} className="btn-primary text-sm px-4 py-2">
                Appoint
              </button>
              <button onClick={onCallback} className="btn-secondary text-sm px-4 py-2">
                Request Callback
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Quote breakdown (collapsible) */}
      {quoteExpanded && firm.quote && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <table className="w-full text-sm">
            <tbody className="divide-y divide-gray-50">
              <tr className="text-gray-600">
                <td className="py-1.5">Base legal fee</td>
                <td className="py-1.5 text-right font-medium">{formatCurrency(firm.quote.base_fee)}</td>
              </tr>
              {firm.quote.adjustments.map((adj) => (
                <tr key={adj.name} className="text-gray-600">
                  <td className="py-1.5 pl-4 text-gray-500">+ {adj.name}</td>
                  <td className="py-1.5 text-right">{formatCurrency(adj.amount)}</td>
                </tr>
              ))}
              <tr className="text-gray-500">
                <td className="py-1.5">VAT (20%)</td>
                <td className="py-1.5 text-right">{formatCurrency(firm.quote.vat)}</td>
              </tr>
              {firm.quote.disbursements.map((d) => (
                <tr key={d.name} className="text-gray-500">
                  <td className="py-1.5 pl-4">
                    {d.name}
                    {d.estimated && <span className="text-gray-400 text-xs ml-1">(est.)</span>}
                  </td>
                  <td className="py-1.5 text-right">{formatCurrency(d.amount)}</td>
                </tr>
              ))}
              <tr className="font-semibold text-gray-900 border-t border-gray-200">
                <td className="pt-2">Total</td>
                <td className="pt-2 text-right">{formatCurrency(firm.quote.total)}</td>
              </tr>
            </tbody>
          </table>
          <p className="text-xs text-gray-400 mt-2">
            Estimates only. Final fee agreed with the firm. Disbursements marked (est.) may vary.
          </p>
        </div>
      )}
    </div>
  );
}
