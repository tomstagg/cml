"use client";

import { useState } from "react";
import { X, Loader2, CheckCircle } from "lucide-react";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import {
  appointmentsApi,
  type FirmResult,
  type IntakeSummary,
  type IntakeSummarySide,
} from "@/lib/api";
import { trackSelect } from "@/lib/analytics";
import { formatCurrency } from "@/lib/utils";

type Props = {
  firm: FirmResult;
  sessionId: string;
  intakeSummary: IntakeSummary;
  onClose: () => void;
};

type FormData = {
  client_name: string;
  client_email: string;
  client_phone: string;
  purchase_property_postcode?: string;
  sale_property_postcode?: string;
  data_sharing_consent: boolean;
};

// Mirrors the backend transaction_details token → human label map in
// app/services/email.py. Kept here too so the UI doesn't round-trip to render.
const DETAIL_LABELS: Record<string, string> = {
  mortgage_required: "Mortgage",
  new_build: "New build",
  new_lease: "New lease",
  shared_ownership_or_help_to_buy: "Shared ownership / Help to Buy",
  gifted_deposit: "Gifted deposit",
  unregistered_title_purchase: "Unregistered title (purchase)",
  additional_mortgage_redemption: "Additional mortgage redemption",
  unregistered_title_sale: "Unregistered title (sale)",
};

const TENURE_LABELS: Record<string, string> = {
  freehold: "Freehold",
  leasehold: "Leasehold",
  unsure: "Not sure yet",
};

const TRANSACTION_LABEL: Record<string, string> = {
  buying: "Buying",
  selling: "Selling",
  selling_and_buying: "Buying & selling",
};

// UK formats — mirror backend POSTCODE_REGEX in chat.py.
const UK_POSTCODE = /^[A-Z]{1,2}[0-9][0-9A-Z]?\s*[0-9][A-Z]{2}$/i;
const UK_PHONE = /^(\+?44\s?|0)\d{9,10}$/; // tolerant: covers 07… mobiles and landlines

function formatDetails(tokens: string[] | undefined): string {
  if (!tokens || tokens.length === 0) return "None selected";
  return tokens.map((t) => DETAIL_LABELS[t] ?? t).join(", ");
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-navy text-right">{value}</span>
    </div>
  );
}

function SidePanel({ heading, side }: { heading: string; side: IntakeSummarySide }) {
  return (
    <div className="flex-1 rounded-lg border border-gray-200 bg-white p-3 space-y-1.5">
      <div className="text-xs uppercase tracking-wide text-gray-500">{heading}</div>
      <SummaryRow
        label="Tenure"
        value={side.tenure ? TENURE_LABELS[side.tenure] ?? side.tenure : "—"}
      />
      <SummaryRow label="Property value" value={formatCurrency(side.value)} />
      <SummaryRow label="Details" value={formatDetails(side.details)} />
    </div>
  );
}

export function SelectModal({ firm, sessionId, intakeSummary, onClose }: Props) {
  const [done, setDone] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isValid, isSubmitting },
  } = useForm<FormData>({
    mode: "onChange",
    defaultValues: {
      purchase_property_postcode: intakeSummary.user_postcode ?? "",
      sale_property_postcode: intakeSummary.user_postcode ?? "",
    },
  });

  const isBuying = !!intakeSummary.buying;
  const isSelling = !!intakeSummary.selling;
  const isCombined = isBuying && isSelling;
  const priceType = firm.quote?.price_type ?? null;
  const priceLabel = priceType === "verified" ? "verified by firm" : "estimated";

  async function onSubmit(data: FormData) {
    try {
      await appointmentsApi.create({
        session_id: sessionId,
        org_id: firm.org_id,
        type: "select",
        client_name: data.client_name,
        client_email: data.client_email,
        client_phone: data.client_phone,
        quoted_price: firm.quote?.total,
        purchase_property_postcode: isBuying
          ? data.purchase_property_postcode?.trim() || undefined
          : undefined,
        sale_property_postcode: isSelling
          ? data.sale_property_postcode?.trim() || undefined
          : undefined,
        price_type: priceType ?? undefined,
        data_sharing_consent: data.data_sharing_consent,
      });
      trackSelect(sessionId, firm.org_id, firm.quote?.total ?? null);
      setDone(true);
    } catch {
      toast.error("Failed to send your details. Please try again.");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl my-8 max-h-[calc(100vh-4rem)] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-100 sticky top-0 bg-white z-10">
          <h2 className="text-lg font-semibold text-navy">
            Send your details to {firm.trading_name}
          </h2>
          <button onClick={onClose} className="btn-ghost p-1" aria-label="Close">
            <X className="w-5 h-5" />
          </button>
        </div>

        {done ? (
          <div className="p-10 text-center">
            <CheckCircle className="w-12 h-12 text-brand-600 mx-auto mb-3" />
            <p className="font-semibold text-navy mb-1">Your details are on their way</p>
            <p className="text-gray-500 text-sm mb-6">
              {firm.trading_name} will contact you directly by the next working day. We&apos;ve
              sent you a copy of the details shared.
            </p>
            <button onClick={onClose} className="btn-primary">
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
            <p className="text-sm text-gray-600">
              You are asking us to send your details to {firm.trading_name} so they can contact
              you about your transaction.
            </p>

            {/* Transaction summary */}
            <section>
              <div className="text-xs uppercase tracking-wide text-gray-500 mb-2">
                Your transaction summary
              </div>
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 space-y-2">
                <SummaryRow
                  label="Transaction"
                  value={
                    TRANSACTION_LABEL[intakeSummary.transaction_type ?? ""] ??
                    "—"
                  }
                />
                {isCombined ? (
                  <div className="flex flex-col sm:flex-row gap-2">
                    {intakeSummary.buying && (
                      <SidePanel heading="Buying" side={intakeSummary.buying} />
                    )}
                    {intakeSummary.selling && (
                      <SidePanel heading="Selling" side={intakeSummary.selling} />
                    )}
                  </div>
                ) : (
                  <>
                    {intakeSummary.buying && (
                      <>
                        <SummaryRow
                          label="Tenure"
                          value={
                            intakeSummary.buying.tenure
                              ? TENURE_LABELS[intakeSummary.buying.tenure] ?? "—"
                              : "—"
                          }
                        />
                        <SummaryRow
                          label="Property value"
                          value={formatCurrency(intakeSummary.buying.value)}
                        />
                        <SummaryRow
                          label="Details"
                          value={formatDetails(intakeSummary.buying.details)}
                        />
                      </>
                    )}
                    {intakeSummary.selling && (
                      <>
                        <SummaryRow
                          label="Tenure"
                          value={
                            intakeSummary.selling.tenure
                              ? TENURE_LABELS[intakeSummary.selling.tenure] ?? "—"
                              : "—"
                          }
                        />
                        <SummaryRow
                          label="Property value"
                          value={formatCurrency(intakeSummary.selling.value)}
                        />
                        <SummaryRow
                          label="Details"
                          value={formatDetails(intakeSummary.selling.details)}
                        />
                      </>
                    )}
                  </>
                )}
                {firm.quote && (
                  <SummaryRow
                    label="Price shown"
                    value={`${formatCurrency(Math.ceil(firm.quote.total))} ${priceLabel}`}
                  />
                )}
              </div>
            </section>

            {/* About this price */}
            <section>
              <div className="text-xs uppercase tracking-wide text-gray-500 mb-2">
                About this price
              </div>
              <div className="rounded-lg border border-gray-200 bg-white p-3 text-sm text-gray-700 space-y-2">
                <p>
                  The price shown for {firm.trading_name} is{" "}
                  {priceType === "verified" ? (
                    <>
                      based on pricing supplied by the firm. It includes standard legal fees,
                      VAT where applicable, HM Land Registry fees and a standard search pack.
                    </>
                  ) : (
                    <>
                      an estimate based on your answers and pricing information published by
                      the firm. It includes standard legal fees, VAT where applicable, HM Land
                      Registry fees and a standard search pack.
                    </>
                  )}
                </p>
                <p>
                  Additional costs may apply if your transaction changes or requires extra work
                  or searches.{" "}
                  <a
                    href="/how-it-works#whats-in-my-price"
                    target="_blank"
                    className="text-brand-600 hover:underline"
                  >
                    What is included in my price?
                  </a>
                </p>
              </div>
            </section>

            {/* Price transparency */}
            <section>
              <div className="text-xs uppercase tracking-wide text-gray-500 mb-2">
                Price transparency
              </div>
              <p className="text-sm text-gray-600">
                Please check whether the final price remains consistent with the price shown
                here. The price may legitimately change if circumstances change, but if that
                happens we expect your firm to explain this to you at the time. We&apos;ll ask
                for feedback later about your experience with {firm.trading_name}, including
                whether the price changed and if you were told about it at the time.
              </p>
            </section>

            {/* Your details */}
            <section className="space-y-3">
              <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">
                Your details
              </div>
              <p className="text-sm text-gray-600">
                Please provide your contact details and the property postcode(s) so we can
                share this with {firm.trading_name}.
              </p>

              <div>
                <label className="label" htmlFor="select_name">
                  Full name *
                </label>
                <input
                  id="select_name"
                  className="input"
                  placeholder="Your full name"
                  autoComplete="name"
                  {...register("client_name", {
                    required: "Name is required",
                    minLength: { value: 2, message: "Name is too short" },
                  })}
                />
                {errors.client_name && (
                  <p className="text-red-500 text-xs mt-1">{errors.client_name.message}</p>
                )}
              </div>

              <div>
                <label className="label" htmlFor="select_email">
                  Email address *
                </label>
                <input
                  id="select_email"
                  className="input"
                  type="email"
                  placeholder="you@example.com"
                  autoComplete="email"
                  {...register("client_email", {
                    required: "Email is required",
                    pattern: {
                      value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                      message: "Please enter a valid email address",
                    },
                  })}
                />
                {errors.client_email && (
                  <p className="text-red-500 text-xs mt-1">{errors.client_email.message}</p>
                )}
              </div>

              <div>
                <label className="label" htmlFor="select_phone">
                  Telephone number *
                </label>
                <input
                  id="select_phone"
                  className="input"
                  type="tel"
                  placeholder="07700 900123"
                  autoComplete="tel"
                  {...register("client_phone", {
                    required: "Phone number is required",
                    pattern: {
                      value: UK_PHONE,
                      message: "Please enter a valid UK phone number",
                    },
                  })}
                />
                {errors.client_phone && (
                  <p className="text-red-500 text-xs mt-1">{errors.client_phone.message}</p>
                )}
              </div>

              {isBuying && (
                <div>
                  <label className="label" htmlFor="select_purchase_postcode">
                    Purchase property postcode
                  </label>
                  <input
                    id="select_purchase_postcode"
                    className="input"
                    placeholder="e.g. B1 1AA"
                    autoComplete="postal-code"
                    {...register("purchase_property_postcode", {
                      validate: (v) =>
                        !v || UK_POSTCODE.test(v.trim()) || "Please enter a valid UK postcode",
                    })}
                  />
                  {errors.purchase_property_postcode && (
                    <p className="text-red-500 text-xs mt-1">
                      {errors.purchase_property_postcode.message}
                    </p>
                  )}
                </div>
              )}

              {isSelling && (
                <div>
                  <label className="label" htmlFor="select_sale_postcode">
                    Sale property postcode
                  </label>
                  <input
                    id="select_sale_postcode"
                    className="input"
                    placeholder="e.g. B1 1AA"
                    autoComplete="postal-code"
                    {...register("sale_property_postcode", {
                      validate: (v) =>
                        !v || UK_POSTCODE.test(v.trim()) || "Please enter a valid UK postcode",
                    })}
                  />
                  {errors.sale_property_postcode && (
                    <p className="text-red-500 text-xs mt-1">
                      {errors.sale_property_postcode.message}
                    </p>
                  )}
                </div>
              )}
            </section>

            {/* Consent */}
            <section>
              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="mt-1 rounded"
                  {...register("data_sharing_consent", { required: true })}
                />
                <span className="text-sm text-gray-700">
                  I consent to Choose My Lawyer sending my name, contact information and
                  transaction details to {firm.trading_name} so they can contact me about
                  acting on this transaction. *
                </span>
              </label>
            </section>

            {/* Next steps */}
            <section className="rounded-lg bg-brand-50/60 border border-brand-100 p-3 text-sm text-navy space-y-2">
              <p>
                <strong>{firm.trading_name}</strong> will contact you directly by the next
                working day.
              </p>
              <p>
                They will first complete a conflict check. If they can act, they should confirm
                this and send their client care letter and terms of business shortly afterwards.
              </p>
              <p>
                We will send you a copy of the details sent to the firm and may follow up to
                check that contact was made.
              </p>
            </section>

            <button
              type="submit"
              disabled={!isValid || isSubmitting}
              className="btn-primary w-full"
            >
              {isSubmitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>Send my details to {firm.trading_name}</>
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
