// Intake-schema constants — mirror backend/app/services/chat.py to keep
// client-side validation aligned with the server's `validate_answer`.

export const CURRENCY_MIN = 50_000;
export const CURRENCY_MAX = 5_000_000;

export function currencyOutOfBoundsMessage(side: "purchase" | "sale"): string {
  return `Can you check that ${side} price please`;
}
