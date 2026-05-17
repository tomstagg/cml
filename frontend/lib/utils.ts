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

// Source data has mixed casing (BIRMINGHAM vs Birmingham, NEWCASTLE UPON TYNE
// vs Newcastle upon Tyne). Title-case for display, keeping the UK convention
// of lowercase connectors ("on", "upon", "under" etc.) when not the first word.
const CITY_STOPWORDS = new Set(["on", "of", "the", "upon", "under", "and", "in", "by"]);

export function formatCityName(s: string | null | undefined): string {
  if (!s) return "";
  return s
    .toLowerCase()
    .split(/(\s+|-)/)
    .map((tok, i) => {
      if (tok === "" || /^\s+$/.test(tok) || tok === "-") return tok;
      if (i > 0 && CITY_STOPWORDS.has(tok)) return tok;
      return tok.charAt(0).toUpperCase() + tok.slice(1);
    })
    .join("");
}

export type SeverityBand = {
  stars: 0 | 1 | 2 | 3 | 4 | 5;
  label: string;
};

/** Map a 0-100 complaints / regulatory score onto the shared severity band
 *  defined in Annex One §5.7.5 (PLAN.md "UI severity bands"). */
export function severityBand(score: number): SeverityBand {
  if (score >= 100) return { stars: 5, label: "No history" };
  if (score >= 80) return { stars: 4, label: "Very low" };
  if (score >= 60) return { stars: 3, label: "Low" };
  if (score >= 40) return { stars: 2, label: "Moderate" };
  if (score >= 20) return { stars: 1, label: "Elevated" };
  return { stars: 0, label: "High" };
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
