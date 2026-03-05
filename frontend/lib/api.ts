/**
 * API client — thin wrapper over fetch with base URL and auth header injection.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
export const sessionsApi = {
  create: (practiceArea = "probate") =>
    request("/api/public/sessions", { method: "POST", body: { practice_area: practiceArea } }),

  get: (sessionId: string) => request(`/api/public/sessions/${sessionId}`),

  answer: (sessionId: string, questionId: string, answer: string | string[]) =>
    request(`/api/public/sessions/${sessionId}/answer`, {
      method: "POST",
      body: { question_id: questionId, answer },
    }),

  save: (sessionId: string, email: string) =>
    request(`/api/public/sessions/${sessionId}/save`, {
      method: "POST",
      body: { email },
    }),
};

// --- Public: Search / Results ---
export const searchApi = {
  getResults: (sessionId: string) => request(`/api/public/search/${sessionId}`),
};

// --- Public: Appointments ---
export const appointmentsApi = {
  create: (data: {
    session_id: string;
    org_id: string;
    type: "appoint" | "callback";
    client_name: string;
    client_email: string;
    client_phone?: string;
    preferred_time?: string;
    quoted_price?: number;
    consent_contacted: boolean;
    consent_terms: boolean;
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
  update: (token: string, data: { website_url?: string; phone?: string; email?: string }) =>
    request("/api/firm/profile", { method: "PATCH", body: data, token }),
};

// --- Firm: Pricing ---
export const firmPricingApi = {
  list: (token: string) => request("/api/firm/pricing", { token }),
  create: (token: string, data: unknown) =>
    request("/api/firm/pricing", { method: "POST", body: data, token }),
  update: (token: string, cardId: string, data: unknown) =>
    request(`/api/firm/pricing/${cardId}`, { method: "PUT", body: data, token }),
  delete: (token: string, cardId: string) =>
    request(`/api/firm/pricing/${cardId}`, { method: "DELETE", token }),
  preview: (token: string, cardId: string) =>
    request(`/api/firm/pricing/${cardId}/preview`, { method: "POST", token }),
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
