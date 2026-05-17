import { API_BASE } from "./api";
import { hasMarketingConsent } from "./consent";

// Standard Meta event names get richer attribution in Ads Manager;
// other events are recorded as custom events.
const META_STANDARD = {
  page_view: "PageView",
  select: "Lead",
  callback: "Contact",
} as const;

const META_CUSTOM = {
  intake_started: "IntakeStarted",
  intake_completed: "IntakeCompleted",
  scorecard_chosen: "ScorecardChosen",
  results_viewed: "ResultsViewed",
} as const;

type EventType = keyof typeof META_STANDARD | keyof typeof META_CUSTOM;

type Fbq = (
  cmd: "track" | "trackCustom" | "init",
  name: string,
  params?: Record<string, unknown>,
) => void;

declare global {
  interface Window {
    fbq?: Fbq;
  }
}

export function trackPageView(page: string, referrer?: string): void {
  emit("page_view", null, { page, referrer });
}

export function trackIntakeStarted(sessionId: string): void {
  emit("intake_started", sessionId, { session_id: sessionId });
}

export function trackIntakeCompleted(sessionId: string): void {
  emit("intake_completed", sessionId, { session_id: sessionId });
}

export function trackScorecardChosen(sessionId: string, preference: string): void {
  emit("scorecard_chosen", sessionId, { session_id: sessionId, preference });
}

export function trackResultsViewed(
  sessionId: string,
  topFiveCount: number,
  fullCount: number,
): void {
  emit("results_viewed", sessionId, {
    session_id: sessionId,
    top_five_count: topFiveCount,
    full_count: fullCount,
  });
}

export function trackSelect(
  sessionId: string,
  orgId: string,
  quotedPrice: number | null,
): void {
  emit("select", sessionId, {
    session_id: sessionId,
    org_id: orgId,
    quoted_price: quotedPrice,
  });
}

export function trackCallback(
  sessionId: string,
  orgIds: string[],
  quotedPrices: (number | null)[],
): void {
  emit("callback", sessionId, {
    session_id: sessionId,
    org_ids: orgIds,
    quoted_prices: quotedPrices,
  });
}

function emit(
  type: EventType,
  sessionId: string | null,
  metadata: Record<string, unknown>,
): void {
  // Pre-consent we ship no tracking — Meta Pixel and the backend mirror
  // are both gated on the user's explicit choice.
  if (!hasMarketingConsent()) return;
  fireMetaPixel(type, metadata);
  mirrorToBackend(type, sessionId, metadata);
}

function fireMetaPixel(type: EventType, metadata: Record<string, unknown>) {
  if (typeof window === "undefined" || !window.fbq) return;

  if (type in META_STANDARD) {
    window.fbq("track", META_STANDARD[type as keyof typeof META_STANDARD], metadata);
  } else {
    window.fbq("trackCustom", META_CUSTOM[type as keyof typeof META_CUSTOM], metadata);
  }
}

function mirrorToBackend(
  type: EventType,
  sessionId: string | null,
  metadata: Record<string, unknown>,
) {
  if (typeof window === "undefined") return;

  fetch(`${API_BASE}/api/public/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ event_type: type, session_id: sessionId, metadata }),
    keepalive: true,
  }).catch(() => {});
}
