// Marketing/analytics consent state. The Meta Pixel and the backend
// analytics_events mirror are both gated on this — in the absence of an
// explicit "accepted" decision we ship no tracking.

export type ConsentState = "accepted" | "rejected";

const KEY = "cml.cookieConsent";
const EVENT = "cml:consent-changed";

export function getConsent(): ConsentState | null {
  if (typeof window === "undefined") return null;
  const v = window.localStorage.getItem(KEY);
  return v === "accepted" || v === "rejected" ? v : null;
}

export function setConsent(state: ConsentState): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(KEY, state);
  window.dispatchEvent(new CustomEvent(EVENT, { detail: state }));
}

export function hasMarketingConsent(): boolean {
  return getConsent() === "accepted";
}

export function onConsentChanged(handler: (state: ConsentState) => void): () => void {
  if (typeof window === "undefined") return () => {};
  const listener = (e: Event) => handler((e as CustomEvent<ConsentState>).detail);
  window.addEventListener(EVENT, listener);
  return () => window.removeEventListener(EVENT, listener);
}
