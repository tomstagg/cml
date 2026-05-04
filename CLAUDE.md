# CLAUDE.md — Choose My Lawyer (CML)

Guidance for Claude Code when working in this repository.

---

## Project overview

Choose My Lawyer is a UK legal comparison platform.
Consumers go through a guided conversational intake and get a ranked list of solicitors with calculated quotes. Firms enrol, manage pricing via a portal, and receive callback requests / instructions ("Proceed") via the platform.

**MVP scope (pilot)**: Residential conveyancing only · West Midlands Combined Authority (WMCA) · Firms manually enrolled + priced · Go-live **1 June 2026** · ~90-day PPC-driven pilot.

Goal of the MVP is commercial validation, not feature completeness — prioritise speed, clarity, and measurability.

Full requirements: `docs/requirements.md` (incl. Annex One — ranking methodology)
Architecture plan: `PLAN.md`

---

## Monorepo structure

```
cml/
├── backend/      # Python 3.12, FastAPI, SQLAlchemy async, Alembic
├── frontend/     # Next.js 15 (App Router), TypeScript, Tailwind CSS
├── docs/         # Functional spec PDF
├── PLAN.md       # Architecture decisions and phase status
└── docker-compose.yml
```

---

## Local development

```bash
# Start everything (PostgreSQL, FastAPI, Next.js)
docker-compose up

# Run DB migrations (first time or after schema changes)
docker-compose exec backend alembic upgrade head

# Access
# Frontend:  http://localhost:3000
# API docs:  http://localhost:8000/api/docs
# API health: http://localhost:8000/health
```

Copy `.env.example` → `.env` and fill in API keys before starting.

---

## Backend

**Stack**: FastAPI · SQLAlchemy (async) · Alembic · PostgreSQL · APScheduler

### Key files
| File | Purpose |
|---|---|
| `app/main.py` | App entrypoint, middleware, router mounts |
| `app/config.py` | Pydantic settings — reads from `.env` |
| `app/database.py` | Async engine, `get_db` session dependency |
| `app/dependencies.py` | `get_current_user` JWT auth dependency |
| `app/models/` | SQLAlchemy ORM models |
| `app/schemas/` | Pydantic request/response schemas |
| `app/services/` | Business logic (chat flow, price calc, search, email, reviews) |
| `app/tasks/review_sync.py` | APScheduler jobs (weekly Google sync, daily review invitations) |
| `alembic/versions/` | DB migrations |
| `scripts/import_sra_csv.py` | One-off SRA data import |

### API structure
- `GET/POST /api/public/*` — unauthenticated (chat sessions, search, appointments, reviews)
- `POST/GET/PATCH /api/firm/*` — JWT-authenticated firm dashboard
- `GET/POST /api/admin/*` — internal admin (enroll firms, sync Google Places)

### Adding a migration
```bash
docker-compose exec backend alembic revision --autogenerate -m "description"
docker-compose exec backend alembic upgrade head
```

### Running the SRA import
```bash
docker-compose exec backend python scripts/import_sra_csv.py \
  --csv /path/to/sra_firms.csv \
  --region "London" \
  --geocode
```

---

## Frontend

**Stack**: Next.js 15 App Router · TypeScript · Tailwind CSS · React Hook Form · Sonner (toasts)

### Key files
| File | Purpose |
|---|---|
| `lib/api.ts` | Typed API client — all fetch calls go here |
| `lib/utils.ts` | `cn()`, `formatCurrency()`, token helpers |
| `app/(marketing)/` | Public marketing pages |
| `app/(public)/` | Consumer chat, results, review form |
| `app/(firm)/` | Firm portal (login, enroll, dashboard, pricing, reviews) |
| `components/chat/` | Chat interface and sub-components |
| `components/results/` | Results table, FirmCard, modals |
| `components/firm/` | Firm layout, PriceCardForm |

### Component conventions
- All interactive/stateful components are `"use client"` — keep page files as server components where possible
- Use `cn()` from `lib/utils` for conditional class merging (clsx + tailwind-merge)
- Toast notifications via `sonner`: `toast.success()`, `toast.error()`
- Forms via `react-hook-form`
- API calls always go through `lib/api.ts` — never raw fetch calls in components

### Brand palette (per requirements)
| Name | HEX |
|---|---|
| Teal | `#0AE5F6` |
| Navy | `#080C64` |
| Mint | `#69E4B5` |
| Purple | `#9747FF` |

The MVP must replicate the Figma prototype journey and screens as closely as reasonably possible, using the corporate logos and colours above.

### Tailwind design system
| Token | Usage |
|---|---|
| `.btn-primary` | Primary action buttons |
| `.btn-secondary` | Secondary/outline buttons |
| `.btn-ghost` | Subtle icon buttons |
| `.card` | White rounded card with border |
| `.input` | Text input fields |
| `.label` | Form labels |

---

## Testing

After making any changes to backend Python code, run ruff format:

```bash
cd backend
uv run ruff format .
```

After making any changes to backend code, run the test suite from `backend/`:

```bash
cd backend
uv run pytest -v
```

All 86 tests must pass before committing. If a test fails, fix the root cause — do not skip or delete the test.

- Tests use a separate `test_cml_db` database created automatically on first run
- Requires PostgreSQL running locally (`docker-compose up`)
- Unit tests cover: auth service, chat service, price calculator
- Integration tests cover: all public and firm API endpoints

---

## Git workflow

- **Active branch**: `dev`
- **Do not** commit to or merge into `main` — main is for production releases only
- Commit message format: concise imperative summary, e.g. `fix: backend Dockerfile editable install` or `feat: add cookie consent banner`
- Always commit to `dev`

---

## Environment variables

All config is in `.env` (local) or Railway environment variables (production).
See `.env.example` for all keys. Key ones:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | asyncpg PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret — must be changed in production |
| `SPARKPOST_API_KEY` | Email sending |
| `GOOGLE_PLACES_API_KEY` | Weekly review sync |
| `FETCHIFY_API_KEY` | UK postcode → lat/lng |
| `APP_URL` | Frontend URL (used in email links) |
| `CORS_ORIGINS` | Comma-separated allowed origins |

---

## Ranking algorithm

Deterministic, rules-based, no runtime AI or subjective judgment. Identical inputs must always produce identical outputs. Full detail in **Annex One** of `docs/requirements.md`.

### Balanced scorecard (default, score out of 100)
| Factor | Weight |
|---|---|
| Reputation | 25% |
| Price | 25% |
| Complaints History (Legal Ombudsman) | 15% |
| Regulatory History (SRA / SDT) | 15% |
| Distance to nearest office (optional) | 10% |
| Number of offices | 10% |

### Prioritised scorecard
User may pick **one** priority factor → that factor weighted **40**; remaining factors share 60 proportionally to their balanced-scorecard order. If the user excludes Distance, weights of remaining factors are proportionally rescaled to sum to 100.

### Critical sequencing rule
1. Rank **all in-scope firms** (signed up or not) across the full market using the chosen scorecard.
2. Then extract the **top 5 contactable** (signed-up) firms from that ranking. Never rank signed-up firms separately — this preserves the "whole of market" / independent positioning.

### Factor mechanics (high level)
- **Reputation**: `Adjusted Rating = rating × (1 + k × ln(reviews + 1))`, `k = 0.025`. Then min-max normalised across the results set (50 if all equal).
- **Price**: `Total Effective Price = legal fees (+ confidence uplift c=0.075 if estimated) + included disbursements (+ d=0.02 if estimated) + applicable VAT`. Then min-max normalised (lower price → higher score).
- **Complaints History (LeO)**: Absolute, base 100. Per-decision deduction = `(severity_score × remedy_amount_score) + 4` (penalty if complaint handling unreasonable). SRA-regulated firms only ("Firm SRA" / "ABS Firm SRA"). Aggregated additively across decisions.
- **Regulatory History (SRA + SDT)**: Absolute, base 100. Predefined deductions per outcome (Rebuke −5 → Band D −60; SDT fines −10 → −60). **An SRA Intervention removes the firm from results entirely.** No floor — score may go negative.
- **Distance**: Optional. Geodesic distance from user postcode to nearest recorded office. Min-max normalised (closer → higher).
- **Number of offices**: Banded absolute score (1 → 70, 2–3 → 78, 4–6 → 85, 7–10 → 90, 11–20 → 95, 21+ → 100).

### Tie-break order
Reputation → Complaints → Regulatory → Price → Distance → Offices → alphabetical.

### Implementation notes
- All factor scores must retain **full numerical precision** internally; only the final overall score is rounded to an integer for display.
- All ingestion / cleansing / normalisation of LeO and SRA data must complete **prior to runtime**. The runtime ranker only consumes pre-processed structured inputs.
- Full results set (below the top 5) must be **sortable by individual factor**; sort is display-only and does not change underlying ranking.

---

## Pricing model

Price cards are stored as JSONB. Canonical schema in `app/schemas/firm.py` (`PriceCardData`); calculator in `app/services/price_calc.py`.

### Sources of price data
- **Quoted Price** — provided directly by the firm via the portal (high confidence).
- **Estimated Price** — interpreted by CML from the firm's published transparency statement and **manually normalised** into the standardised database before go-live. No probabilistic / AI pricing at runtime.

### Total Effective Price
```
P_effective = P_legal_effective + (P_legal_effective × VAT) + P_included_disbursements
```
Where:
- `P_legal_effective = P_quoted` for quoted prices, or `P_estimated × (1 + c)` for estimated prices, with `c = 0.075`.
- Included disbursements are stored exclusive of VAT with a per-item VAT flag; the aggregate is supplied with VAT already applied as appropriate.
- A confidence factor `d = 0.02` is applied where included disbursements are estimated/system-derived.
- **Excluded disbursements** (conditional / not determinable at intake) do not enter the ranking price and must be flagged to the user with a link to the CML explainer page.

### Conveyancing price card (illustrative — confirm against `PriceCardData` before edits)
```json
{
  "practice_area": "conveyancing",
  "matter_types": ["purchase", "sale", "remortgage"],
  "legal_fees": [{"property_value_min": 0, "property_value_max": 250000, "fee": 950}],
  "adjustments": [{"name": "Leasehold supplement", "amount": 250, "condition": "leasehold"}],
  "included_disbursements": [{"name": "Land Registry fee", "amount": 150, "vat_applies": false, "estimated": false}],
  "vat_applies_to_fees": true,
  "price_type": "quoted"
}
```

---

## User actions, notifications & billing (pilot)

### Consumer actions on results
- **Proceed** — instructs a single firm. Confirmatory form captures name + email. Auto-email sent to the firm **in the user's name** (not in CML's name), copy to user. Lead recorded with timestamp.
- **Request a callback** — up to **5 firms**. Confirmatory form captures name, email, phone, and availability over next two working days. Same email-in-user's-name rule.

### Email notification cycle
- Lead emails on Proceed / Callback (firm + user copy).
- Callback follow-up to user **end of same working day** as scheduled callback (binary "did the firm contact you?").
- Proceed follow-up to user **5 working days** after action.
- Conflict-check failure: firm notifies CML → user emailed immediately with link back to results.
- Feedback request to user **2 months** after Proceed for review capture.

### Billing
Manual for the pilot. Chargeable events (Proceed / Callback) recorded and exported for periodic invoicing after a delay window (allowing firms time to make contact). Automated billing deferred to full launch.

---

## Analytics & marketing tracking

- **Meta Pixel** is mandatory across all pages and must fire on: page view, search completion, results page view, Proceed, Callback request. Events must support conversion tracking, retargeting audiences, and campaign optimisation.
- Funnel + drop-off + conversion analytics required (third-party tooling acceptable; no custom dashboard needed for MVP).
- All event captures must include timestamp, session ID, and relevant inputs.
- Data must be exportable (e.g. CSV) so the founder can analyse independently.

---

## Deferred (do not implement unless asked)

- Practice areas other than residential conveyancing (incl. probate)
- Geographies outside the West Midlands Combined Authority
- National rollout features
- Advanced UX/UI refinement beyond the Figma prototype
- AI / probabilistic pricing at runtime
- Case-management system integrations
- Automated firm onboarding flows
- Payment handling (Stripe / Xero / PSP)
- Facebook / Trustpilot review aggregation
- Admin moderation UI
- Voice input
- Welsh language
