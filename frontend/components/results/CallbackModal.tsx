"use client";

import { useState } from "react";
import { X, Loader2, CheckCircle } from "lucide-react";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import {
  callbacksApi,
  type CallbackWindow,
  type FirmResult,
  type IntakeSummary,
} from "@/lib/api";
import { trackCallback } from "@/lib/analytics";
import { formatCurrency } from "@/lib/utils";

type Props = {
  firms: FirmResult[]; // 1..3, pre-selected on the results page
  sessionId: string;
  intakeSummary: IntakeSummary;
  onClose: () => void;
  onSuccess: () => void;
};

type FormData = {
  client_name: string;
  client_email: string;
  client_phone: string;
  preferred_callback_window: CallbackWindow;
  data_sharing_consent: boolean;
};

const UK_PHONE = /^(\+?44\s?|0)\d{9,10}$/;

const WINDOW_OPTIONS: { value: CallbackWindow; label: string }[] = [
  { value: "09:00-11:00", label: "9am – 11am" },
  { value: "11:00-13:00", label: "11am – 1pm" },
  { value: "13:00-15:00", label: "1pm – 3pm" },
  { value: "15:00-17:00", label: "3pm – 5pm" },
];

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

function formatDetails(tokens: string[] | undefined): string {
  if (!tokens || tokens.length === 0) return "None selected";
  return tokens.map((t) => DETAIL_LABELS[t] ?? t).join(", ");
}

function priceLabel(t: "estimated" | "verified" | undefined): string {
  return t === "verified" ? "verified by firm" : "estimated";
}

function explanationText(types: ("estimated" | "verified" | undefined)[]): string {
  const allVerified = types.every((t) => t === "verified");
  const allEstimated = types.every((t) => t === "estimated" || t === undefined);
  if (allVerified)
    return "The prices shown are based on pricing supplied by the firms. They include standard legal fees, VAT where applicable, HM Land Registry fees and a standard search pack.";
  if (allEstimated)
    return "The prices shown are estimates based on your answers and pricing information published by the firms. They include standard legal fees, VAT where applicable, HM Land Registry fees and a standard search pack.";
  return "Some prices shown are based on verified pricing supplied directly by firms, while others are estimated using pricing information published by firms. All prices include standard legal fees, VAT where applicable, HM Land Registry fees and a standard search pack.";
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-navy text-right">{value}</span>
    </div>
  );
}

export function CallbackModal({
  firms,
  sessionId,
  intakeSummary,
  onClose,
  onSuccess,
}: Props) {
  const [done, setDone] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isValid, isSubmitting },
  } = useForm<FormData>({ mode: "onChange" });

  const priceTypes = firms.map((f) => f.quote?.price_type);
  const isCombined = !!intakeSummary.buying && !!intakeSummary.selling;
  const canSubmit = firms.length >= 1;

  async function onSubmit(data: FormData) {
    try {
      await callbacksApi.createBulk({
        session_id: sessionId,
        client_name: data.client_name,
        client_email: data.client_email,
        client_phone: data.client_phone,
        preferred_callback_window: data.preferred_callback_window,
        data_sharing_consent: true,
        firms: firms.map((f) => ({
          org_id: f.org_id,
          quoted_price: f.quote?.total,
          price_type: f.quote?.price_type,
        })),
      });
      trackCallback(
        sessionId,
        firms.map((f) => f.org_id),
        firms.map((f) => f.quote?.total ?? null),
      );
      setDone(true);
      onSuccess();
    } catch {
      toast.error("Failed to submit your request. Please try again.");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl my-8 max-h-[calc(100vh-4rem)] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-100 sticky top-0 bg-white z-10">
          <h2 className="text-lg font-semibold text-navy">Request callbacks</h2>
          <button onClick={onClose} className="btn-ghost p-1" aria-label="Close">
            <X className="w-5 h-5" />
          </button>
        </div>

        {done ? (
          <div className="p-10 text-center">
            <CheckCircle className="w-12 h-12 text-brand-600 mx-auto mb-3" />
            <p className="font-semibold text-navy mb-1">Callback requests sent</p>
            <p className="text-gray-500 text-sm mb-6">
              The selected firms will aim to contact you during your chosen
              window. We&apos;ve sent you a copy of the details shared.
            </p>
            <button onClick={onClose} className="btn-primary">
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
            <section>
              <p className="text-sm text-gray-600 mb-2">
                You are asking the following firms to contact you about your
                transaction:
              </p>
              <ul className="list-disc pl-5 text-sm text-navy space-y-0.5">
                {firms.map((f) => (
                  <li key={f.org_id}>{f.trading_name}</li>
                ))}
              </ul>
              <p className="text-xs text-gray-500 mt-2">
                You can request callbacks from up to 3 firms from this set of
                results.
              </p>
            </section>

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
                {intakeSummary.buying && (
                  <div className="space-y-1.5">
                    {isCombined && (
                      <div className="text-xs uppercase tracking-wide text-gray-500">
                        Buying
                      </div>
                    )}
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
                  </div>
                )}
                {intakeSummary.selling && (
                  <div className="space-y-1.5">
                    {isCombined && (
                      <div className="text-xs uppercase tracking-wide text-gray-500">
                        Selling
                      </div>
                    )}
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
                  </div>
                )}
              </div>
            </section>

            <section>
              <div className="text-xs uppercase tracking-wide text-gray-500 mb-2">
                Price summary
              </div>
              <div className="rounded-lg border border-gray-200 bg-white divide-y divide-gray-100 text-sm">
                {firms.map((f) => (
                  <div
                    key={f.org_id}
                    className="flex justify-between px-3 py-2"
                  >
                    <span className="text-navy">{f.trading_name}</span>
                    <span className="text-gray-700">
                      {f.quote
                        ? formatCurrency(Math.ceil(f.quote.total))
                        : "—"}{" "}
                      <span className="text-gray-500">
                        {priceLabel(f.quote?.price_type)}
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </section>

            <section>
              <div className="text-xs uppercase tracking-wide text-gray-500 mb-2">
                About these prices
              </div>
              <div className="rounded-lg border border-gray-200 bg-white p-3 text-sm text-gray-700 space-y-2">
                <p>{explanationText(priceTypes)}</p>
                <p>
                  Additional costs may apply if your transaction changes or
                  requires extra work or searches.
                </p>
                <p className="space-x-3">
                  <a
                    href="/how-it-works#whats-in-my-price"
                    target="_blank"
                    className="text-brand-600 hover:underline"
                  >
                    What is included in my price?
                  </a>
                  <a
                    href="/how-it-works#questions-to-ask"
                    target="_blank"
                    className="text-brand-600 hover:underline"
                  >
                    Questions to ask a conveyancing lawyer before instructing
                    them
                  </a>
                </p>
              </div>
            </section>

            <section className="space-y-3">
              <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">
                Your details
              </div>
              <div>
                <label className="label" htmlFor="cb_name">
                  Full name *
                </label>
                <input
                  id="cb_name"
                  className="input"
                  autoComplete="name"
                  placeholder="Your full name"
                  {...register("client_name", {
                    required: "Name is required",
                    minLength: { value: 2, message: "Name is too short" },
                  })}
                />
                {errors.client_name && (
                  <p className="text-red-500 text-xs mt-1">
                    {errors.client_name.message}
                  </p>
                )}
              </div>
              <div>
                <label className="label" htmlFor="cb_email">
                  Email address *
                </label>
                <input
                  id="cb_email"
                  className="input"
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  {...register("client_email", {
                    required: "Email is required",
                    pattern: {
                      value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                      message: "Please enter a valid email address",
                    },
                  })}
                />
                {errors.client_email && (
                  <p className="text-red-500 text-xs mt-1">
                    {errors.client_email.message}
                  </p>
                )}
              </div>
              <div>
                <label className="label" htmlFor="cb_phone">
                  Telephone number *
                </label>
                <input
                  id="cb_phone"
                  className="input"
                  type="tel"
                  autoComplete="tel"
                  placeholder="07700 900123"
                  {...register("client_phone", {
                    required: "Phone number is required",
                    pattern: {
                      value: UK_PHONE,
                      message: "Please enter a valid UK phone number",
                    },
                  })}
                />
                {errors.client_phone && (
                  <p className="text-red-500 text-xs mt-1">
                    {errors.client_phone.message}
                  </p>
                )}
              </div>

              <fieldset>
                <legend className="label">Preferred callback window *</legend>
                <div className="grid grid-cols-2 gap-2 mt-1">
                  {WINDOW_OPTIONS.map((o) => (
                    <label
                      key={o.value}
                      className="flex items-center gap-2 text-sm cursor-pointer rounded-md border border-gray-200 px-3 py-2 hover:border-navy/40"
                    >
                      <input
                        type="radio"
                        value={o.value}
                        {...register("preferred_callback_window", {
                          required: "Please choose a window",
                        })}
                      />
                      {o.label}
                    </label>
                  ))}
                </div>
                {errors.preferred_callback_window && (
                  <p className="text-red-500 text-xs mt-1">
                    {errors.preferred_callback_window.message}
                  </p>
                )}
              </fieldset>
            </section>

            <section>
              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="mt-1 rounded"
                  {...register("data_sharing_consent", { required: true })}
                />
                <span className="text-sm text-gray-700">
                  I consent to Choose My Lawyer sending my name, contact
                  information and transaction details to the selected firms so
                  they can contact me about this transaction. *
                </span>
              </label>
            </section>

            <section className="rounded-lg bg-brand-50/60 border border-brand-100 p-3 text-sm text-navy space-y-2">
              <p>
                The selected firms will aim to contact you during your chosen
                callback window where possible.
              </p>
              <p>
                If contact is unsuccessful, firms will make one further attempt
                during normal business hours on the following working day.
              </p>
              <p>
                Firms will first complete conflict checks before confirming
                whether they can act.
              </p>
              <p>
                We will send you a copy of the details sent to the selected
                firms and may follow up to check whether contact was made.
              </p>
            </section>

            <button
              type="submit"
              disabled={!isValid || isSubmitting || !canSubmit}
              className="btn-primary w-full"
            >
              {isSubmitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                "Request callbacks"
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
