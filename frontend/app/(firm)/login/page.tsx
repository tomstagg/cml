"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Scale } from "lucide-react";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { firmAuthApi } from "@/lib/api";
import { setStoredToken } from "@/lib/utils";
import Link from "next/link";

type FormData = { email: string; password: string };

export default function FirmLoginPage() {
  const router = useRouter();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>();

  async function onSubmit(data: FormData) {
    try {
      const res = await firmAuthApi.login(data.email, data.password) as { access_token: string };
      setStoredToken(res.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      toast.error(err.detail || "Invalid email or password");
    }
  }

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-64px)] p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <Scale className="w-10 h-10 text-brand-600 mx-auto mb-3" />
          <h1 className="text-2xl font-bold text-gray-900">Firm Login</h1>
          <p className="text-gray-500 mt-1">Access your Choose My Lawyer dashboard</p>
        </div>

        <div className="card p-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="label">Email</label>
              <input
                className="input"
                type="email"
                placeholder="firm@example.com"
                {...register("email", { required: "Email is required" })}
              />
              {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
            </div>
            <div>
              <label className="label">Password</label>
              <input
                className="input"
                type="password"
                placeholder="••••••••"
                {...register("password", { required: "Password is required" })}
              />
              {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
            </div>
            <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
              {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Sign In"}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-gray-500 mt-4">
          Don't have an account?{" "}
          <Link href="/for-firms" className="text-brand-600 hover:underline">
            Learn how to enroll
          </Link>
        </p>
      </div>
    </div>
  );
}
