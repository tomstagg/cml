import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number, currency = "GBP"): string {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatRating(rating: number | null | undefined): string {
  if (rating === null || rating === undefined) return "No reviews";
  return rating.toFixed(1);
}

export function getAuthStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case "authorised":
      return "text-green-700 bg-green-50 border-green-200";
    case "conditions":
    case "conditions of recognition":
      return "text-amber-700 bg-amber-50 border-amber-200";
    case "revoked":
    case "closed":
      return "text-red-700 bg-red-50 border-red-200";
    default:
      return "text-gray-700 bg-gray-50 border-gray-200";
  }
}

export function getAuthStatusLabel(status: string): string {
  switch (status.toLowerCase()) {
    case "authorised":
      return "SRA Authorised";
    case "conditions":
      return "Conditions Apply";
    case "revoked":
      return "Revoked";
    default:
      return status;
  }
}

/** Get a token from localStorage (client-side only). */
export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("cml_firm_token");
}

export function setStoredToken(token: string): void {
  localStorage.setItem("cml_firm_token", token);
}

export function clearStoredToken(): void {
  localStorage.removeItem("cml_firm_token");
}
