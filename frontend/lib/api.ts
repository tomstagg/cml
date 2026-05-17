/**
 * API client — thin wrapper over fetch with base URL and auth header injection.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string;
  headers?: Record<string, string>;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, token, headers = {} } = options;

  const init: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  };

  const res = await fetch(`${API_BASE}${path}`, init);

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, error.detail || "Request failed");
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

// --- Public: Chat sessions ---
export type AnswerValue =
  | string
  | number
  | string[]
  | Record<string, string | number>;

export const sessionsApi = {
  create: (practiceArea = "residential_conveyancing") =>
    request("/api/public/sessions", { method: "POST", body: { practice_area: practiceArea } }),

  schema: () => request("/api/public/sessions/schema"),

  get: (sessionId: string) => request(`/api/public/sessions/${sessionId}`),

  answer: (sessionId: string, questionId: string, answer: AnswerValue) =>
    request(`/api/public/sessions/${sessionId}/answer`, {
      method: "POST",
      body: { question_id: questionId, answer },
    }),

  updateAnswer: (sessionId: string, questionId: string, answer: AnswerValue) =>
    request(`/api/public/sessions/${sessionId}/answer`, {
      method: "PATCH",
      body: { question_id: questionId, answer },
    }),

  save: (sessionId: string, email: string) =>
    request(`/api/public/sessions/${sessionId}/save`, {
      method: "POST",
      body: { email },
    }),
};

// --- Public: Search / Results ---
export type QuoteBreakdown = {
  base_fee: number;
  adjustments: { name: string; amount: number }[];
  fees_subtotal: number;
  vat: number;
  disbursements: { name: string; amount: number; estimated: boolean }[];
  disbursements_total: number;
  total: number;
  currency: string;
  pricing_model: string;
  price_type: "estimated" | "verified";
};

export type IntakeSummarySide = {
  tenure: "freehold" | "leasehold" | "unsure" | null;
  value: number;
  details: string[];
};

export type IntakeSummary = {
  transaction_type: "buying" | "selling" | "selling_and_buying" | null;
  user_postcode: string | null;
  buying: IntakeSummarySide | null;
  selling: IntakeSummarySide | null;
};

export type FactorScores = {
  reputation: number;
  price: number | null;
  complaints: number;
  regulatory: number;
  distance: number | null;
  offices: number;
};

export type FirmResult = {
  rank: number;
  org_id: string;
  cml_firm_id: string;
  name: string;
  trading_name: string;
  sra_number: string;
  enrolled: boolean;
  google_rating: number | null;
  google_review_count: number | null;
  google_reviews_url: string | null;
  postcode: string | null;
  city: string | null;
  distance_km: number | null;
  office_count: number;
  quote: QuoteBreakdown | null;
  factor_scores: FactorScores | null;
  complaints_url: string | null;
  regulatory_url: string | null;
  score: number;
};

export type SearchResponse = {
  session_id: string;
  results: FirmResult[];
  top_five_contactable: FirmResult[];
  total: number;
  postcode: string | null;
  scorecard_preference: string;
  include_distance: boolean;
  intake_summary: IntakeSummary;
};

export const searchApi = {
  getResults: (
    sessionId: string,
    opts: { scorecard_preference?: string; include_distance?: boolean } = {},
  ) => {
    const params = new URLSearchParams();
    if (opts.scorecard_preference) params.set("scorecard_preference", opts.scorecard_preference);
    if (opts.include_distance !== undefined)
      params.set("include_distance", String(opts.include_distance));
    const qs = params.toString();
    return request<SearchResponse>(
      `/api/public/search/${sessionId}${qs ? `?${qs}` : ""}`,
    );
  },
};

// --- Public: Appointments ---
export const appointmentsApi = {
  create: (data: {
    session_id: string;
    org_id: string;
    type: "select" | "callback";
    client_name: string;
    client_email: string;
    client_phone?: string;
    preferred_time?: string;
    quoted_price?: number;
    // Legacy callback consents.
    consent_contacted?: boolean;
    consent_terms?: boolean;
    // Select-only fields.
    data_sharing_consent?: boolean;
    purchase_property_postcode?: string;
    sale_property_postcode?: string;
    price_type?: "estimated" | "verified";
  }) => request("/api/public/appointments", { method: "POST", body: data }),
};

// --- Public: Reviews ---
export const reviewsApi = {
  getInvitation: (token: string) => request(`/api/public/reviews/invitation/${token}`),

  submit: (data: { token: string; rating: number; text: string; reviewer_name?: string }) =>
    request("/api/public/reviews", { method: "POST", body: data }),
};

// --- Firm: Auth ---
export const firmAuthApi = {
  register: (data: {
    enrollment_token: string;
    email: string;
    password: string;
    full_name: string;
    accept_terms: boolean;
  }) => request("/api/firm/auth/register", { method: "POST", body: data }),

  login: (email: string, password: string) =>
    request("/api/firm/auth/login", { method: "POST", body: { email, password } }),

  me: (token: string) => request("/api/firm/auth/me", { token }),
};

// --- Firm: Profile ---
export const firmProfileApi = {
  get: (token: string) => request("/api/firm/profile", { token }),
  update: (token: string, data: { phone?: string; referral_email?: string }) =>
    request("/api/firm/profile", { method: "PATCH", body: data, token }),
};

// --- Firm: Pricing ---
// Master Export anchor-point shape — see backend/app/schemas/firm.py::PriceCardData.
export type AnchorPrices = Record<string, number | null>;

export type PriceCardData = {
  freehold: { purchase: AnchorPrices; sale: AnchorPrices };
  leasehold: { purchase: AnchorPrices; sale: AnchorPrices };
  modifiers: { name: string; amount: number }[];
  additional_costs: { name: string; amount: number }[];
  disbursements: { name: string; amount: number }[];
};

export type PriceCard = {
  id: string;
  org_id: string;
  price_type: "estimated" | "verified" | "no_data";
  pricing: PriceCardData;
  updated_at: string;
};

export const firmPricingApi = {
  get: (token: string) => request<PriceCard | null>("/api/firm/pricing", { token }),
  upsert: (token: string, data: PriceCardData) =>
    request<PriceCard>("/api/firm/pricing", { method: "PUT", body: data, token }),
  preview: (token: string) =>
    request("/api/firm/pricing/preview", { method: "POST", token }),
};

// --- Firm: Dashboard ---
export const firmDashboardApi = {
  getStats: (token: string) => request("/api/firm/dashboard/stats", { token }),
};

// --- Firm: Reviews ---
export const firmReviewsApi = {
  list: (token: string) => request("/api/firm/reviews", { token }),
  respond: (token: string, reviewId: string, responseText: string) =>
    request(`/api/firm/reviews/${reviewId}/respond`, {
      method: "POST",
      body: { response_text: responseText },
      token,
    }),
  report: (token: string, reviewId: string, reason: string) =>
    request(`/api/firm/reviews/${reviewId}/report`, {
      method: "POST",
      body: { reason },
      token,
    }),
};
