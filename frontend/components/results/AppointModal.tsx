"use client";

import { useState } from "react";
import { X, Loader2, CheckCircle } from "lucide-react";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { appointmentsApi } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

type Props = {
  firm: {
    org_id: string;
    name: string;
    quote: { total: number } | null;
  };
  sessionId: string;
  onClose: () => void;
};

type FormData = {
  client_name: string;
  client_email: string;
  consent_contacted: boolean;
  consent_terms: boolean;
};

export function AppointModal({ firm, sessionId, onClose }: Props) {
  const [done, setDone] = useState(false);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>();

  async function onSubmit(data: FormData) {
    try {
      await appointmentsApi.create({
        session_id: sessionId,
        org_id: firm.org_id,
        type: "appoint",
        client_name: data.client_name,
        client_email: data.client_email,
        quoted_price: firm.quote?.total,
        consent_contacted: data.consent_contacted,
        consent_terms: data.consent_terms,
      });
      setDone(true);
    } catch {
      toast.error("Failed to submit appointment. Please try again.");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="text-lg font-semibold">Appoint {firm.name}</h2>
          <button onClick={onClose} className="btn-ghost p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {done ? (
          <div className="p-6 text-center">
            <CheckCircle className="w-12 h-12 text-brand-600 mx-auto mb-3" />
            <p className="font-semibold text-gray-900 mb-1">Appointment submitted!</p>
            <p className="text-gray-500 text-sm mb-4">
              {firm.name} has been notified and will be in touch to confirm your appointment.
            </p>
            <button onClick={onClose} className="btn-primary">Done</button>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
            {firm.quote && (
              <div className="bg-brand-50 rounded-lg p-3 text-center">
                <p className="text-sm text-gray-600">Estimated total</p>
                <p className="text-2xl font-bold text-brand-700">{formatCurrency(firm.quote.total)}</p>
              </div>
            )}

            <div>
              <label className="label" htmlFor="appoint_name">Full Name *</label>
              <input
                id="appoint_name"
                className="input"
                placeholder="Your full name"
                {...register("client_name", { required: "Name is required" })}
              />
              {errors.client_name && <p className="text-red-500 text-xs mt-1">{errors.client_name.message}</p>}
            </div>

            <div>
              <label className="label" htmlFor="appoint_email">Email Address *</label>
              <input
                id="appoint_email"
                className="input"
                type="email"
                placeholder="you@example.com"
                {...register("client_email", {
                  required: "Email is required",
                  pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Invalid email" },
                })}
              />
              {errors.client_email && <p className="text-red-500 text-xs mt-1">{errors.client_email.message}</p>}
            </div>

            <div className="space-y-2 pt-2">
              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="mt-1 rounded"
                  {...register("consent_contacted", { required: true })}
                />
                <span className="text-sm text-gray-600">
                  I consent to {firm.name} contacting me about this matter *
                </span>
              </label>
              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="mt-1 rounded"
                  {...register("consent_terms", { required: true })}
                />
                <span className="text-sm text-gray-600">
                  I agree to the{" "}
                  <a href="/terms" target="_blank" className="text-brand-600 hover:underline">
                    terms of service
                  </a>{" "}
                  *
                </span>
              </label>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary w-full"
            >
              {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Confirm Appointment"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
