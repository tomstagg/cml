"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, CheckCircle } from "lucide-react";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { firmAuthApi } from "@/lib/api";
import { setStoredToken } from "@/lib/utils";

type FormData = {
  email: string;
  password: string;
  confirm_password: string;
  full_name: string;
  accept_terms: boolean;
};

export default function EnrollPage({ params }: { params: { token: string } }) {
  const router = useRouter();
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormData>();

  async function onSubmit(data: FormData) {
    try {
      const res = await firmAuthApi.register({
        enrollment_token: params.token,
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        accept_terms: data.accept_terms,
      }) as { access_token: string };
      setStoredToken(res.access_token);
      toast.success("Account created! Welcome to Choose My Lawyer.");
      router.push("/firm/dashboard");
    } catch (err: any) {
      toast.error(err.detail || "Registration failed. Please try again.");
    }
  }

  const password = watch("password");

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-64px)] p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Create Your Firm Account</h1>
          <p className="text-gray-500 mt-1">
            Join Choose My Lawyer and start receiving client enquiries.
          </p>
        </div>

        <div className="card p-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="label">Full Name *</label>
              <input
                className="input"
                placeholder="Your name"
                {...register("full_name", { required: "Name is required" })}
              />
              {errors.full_name && <p className="text-red-500 text-xs mt-1">{errors.full_name.message}</p>}
            </div>

            <div>
              <label className="label">Email Address *</label>
              <input
                className="input"
                type="email"
                placeholder="you@firmname.co.uk"
                {...register("email", { required: "Email is required" })}
              />
              {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="label">Password *</label>
              <input
                className="input"
                type="password"
                placeholder="Minimum 8 characters"
                {...register("password", {
                  required: "Password is required",
                  minLength: { value: 8, message: "At least 8 characters" },
                })}
              />
              {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
            </div>

            <div>
              <label className="label">Confirm Password *</label>
              <input
                className="input"
                type="password"
                placeholder="Repeat password"
                {...register("confirm_password", {
                  required: true,
                  validate: (v) => v === password || "Passwords do not match",
                })}
              />
              {errors.confirm_password && (
                <p className="text-red-500 text-xs mt-1">{errors.confirm_password.message}</p>
              )}
            </div>

            <label className="flex items-start gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="mt-1 rounded"
                {...register("accept_terms", { required: "You must accept the terms" })}
              />
              <span className="text-sm text-gray-600">
                I accept the{" "}
                <a href="/terms" target="_blank" className="text-brand-600 hover:underline">
                  Terms of Service
                </a>{" "}
                and{" "}
                <a href="/privacy" target="_blank" className="text-brand-600 hover:underline">
                  Privacy Policy
                </a>{" "}
                *
              </span>
            </label>
            {errors.accept_terms && (
              <p className="text-red-500 text-xs">{errors.accept_terms.message}</p>
            )}

            <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
              {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create Account"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
