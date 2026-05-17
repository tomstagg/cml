# Choose My Lawyer

UK legal comparison platform. The **MVP pilot** is scoped to **residential conveyancing** in the **West Midlands Combined Authority** (go-live 1 June 2026, ~90-day PPC-driven pilot). Consumers answer a short pathway-aware intake (4–5 steps depending on whether they're buying, selling, or doing both) and receive a ranked list of solicitors with calculated Total Effective Prices. Firms enrol, configure pricing, and receive Proceed / Callback requests via the platform. The firm dataset — including pre-computed reputation, complaints and regulatory scores — is curated in the Master Export workbook and ingested by a single importer; admins flag exclusions, enablement, and pilot participation in that workbook.

See `PLAN.md` for architecture decisions and phase status, and `docs/requirements.md` (incl. **Annex One** — ranking methodology) for the full functional spec.

---

## Architecture Overview

```
Browser ──► Next.js 15 (App Router)  ──► FastAPI (async)  ──► PostgreSQL 16
                 (frontend/)                  (backend/)
                   Port 3000                 Port 8000          Port 5432
```

- Frontend proxies `/api/*` to backend via `next.config.ts` rewrites
- Backend uses async SQLAlchemy + asyncpg driver
- APScheduler runs in-process for background jobs (no queue/worker service)

---

## Backend

**Stack**: Python 3.12 · FastAPI · SQLAlchemy async · Alembic · APScheduler · PostgreSQL

**Key files**:

| File | Purpose |
|---|---|
| `app/main.py` | Entrypoint, middleware, router mounts, APScheduler lifecycle |
| `app/config.py` | Pydantic settings (all env vars) |
| `app/database.py` | Async engine, `get_db` session dependency |
| `app/dependencies.py` | `get_current_user` JWT auth dependency |
| `app/models/` | SQLAlchemy ORM models |
| `app/schemas/` | Pydantic request/response schemas |
| `app/services/` | Business logic |
| `app/tasks/scheduler.py` | APScheduler entrypoint (started by the FastAPI lifespan handler) |
| `app/tasks/followups.py` | Follow-up jobs registered into the scheduler (callback EOD, 5-WD Proceed, 2-month feedback) |

**API namespaces**:

- `GET/POST /api/public/*` — unauthenticated (chat, search, appointments, reviews)
- `POST/GET/PATCH /api/firm/*` — JWT Bearer (firm dashboard, pricing, reviews)
- `GET/POST /api/admin/*` — internal only; every route requires the `X-Admin-Key` header (env var `ADMIN_API_KEY`)

**Services**:

| Service | Purpose |
|---|---|
| `auth.py` | bcrypt hashing, JWT sign/verify (24hr expiry) |
| `chat.py` | Pathway-aware conveyancing intake engine (Buying / Selling / Both) + intake flag normalisation for the pricing engine |
| `price_calc.py` | Total Effective Price calculation from JSONB pricing + intake flags; applies the §10 estimated-price uplift (`c = 0.075`) for `price_type=estimated` cards |
| `ranking.py` | Pure factor scorers (Annex One §5–9): reputation, price, complaints, regulatory, distance, offices |
| `scorecard.py` | Weight tables (balanced + 6 prioritised) and tie-broken `apply()` (Annex One §11, §16) |
| `search.py` | Full-market 6-factor ranking + top-5 contactable extraction (Annex One §3.5) |
| `geocoding.py` | Fetchify.io postcode → lat/lng |
| `email.py` | Sparkpost transactional emails (mocked if no key); Proceed/Callback senders dispatch in the user's name with `reply_to` + CML BCC |
| `followup_tokens.py` | HMAC-signed yes/no tokens for one-click follow-up replies |

**Ranking algorithm** — deterministic six-factor scorecard (Annex One §5–11). Each factor is scored 0–100 at full numerical precision; the overall score is a weighted sum and only the displayed integer is rounded. Reputation, complaints and regulatory scores arrive pre-computed from the Master Export workbook and are consumed verbatim by the runtime ranker (Annex One: "all ingestion / cleansing / normalisation must complete prior to runtime").

| Factor | Source data | Score basis | Balanced weight |
|---|---|---|---|
| Reputation | `organisations.adjusted_reputation_value` (pre-baked in Master Export from `ARV = rating × (1 + 0.025 × ln(reviews + 1))`) | min–max normalised across the results set (50 if all equal) | 25% |
| Price | `price_cards` JSONB → Total Effective Price | `(P_max − P) / (P_max − P_min) × 100` (lower price → higher score) | 25% |
| Complaints | `complaints_summary.score` (single row per firm, pre-computed from LeO) | consumed directly as the 0–100 factor score | 15% |
| Regulatory | `regulatory_summary.score` (single row per firm, pre-computed from SRA + SDT) | consumed directly as the 0–100 factor score | 15% |
| Distance | `offices.lat/lng` vs the user's postcode | min–max normalised (closer → higher); user can opt out by leaving the postcode question blank | 10% |
| Offices | `count(offices)` | banded: 1→70, 2–3→78, 4–6→85, 7–10→90, 11–20→95, 21+→100 | 10% |

**Prioritised scorecard** — the user can pick one priority factor on the chat preference step. That factor's weight becomes 40; the other five share 60 in their balanced-scorecard ratios (e.g. Reputation Priority: rep 40, price 20, complaints 12, regulatory 12, distance 8, offices 8). The seven weight sets are pinned verbatim from Annex One §16.6 in `scorecard.py::SCORECARDS`.

**Distance excluded (§8.2)** — if the user opts out of distance, its weight goes to 0 and the remaining factors are proportionately rescaled so the sum stays at 100.

**Sequencing rule (§3.5)** — the *entire* in-scope WMCA market is ranked first using the chosen scorecard. The top-5 contactable firms are then extracted from that ordering by filtering on `enrolled=true AND active_in_pilot=true`. Enrolled firms are never ranked separately — this preserves the "whole of market / fully independent" positioning.

**Eligibility filter (§8.13)** — firms with `organisations.excluded=true` are removed from results entirely before ranking. This is the broader of (a) SRA Intervention and (b) any other CML safeguarding decision recorded in the Master Export. Firms whose price card is `price_type='no_data'` are also excluded at runtime — they have no anchor prices and therefore cannot be priced until a transparency statement is captured.

**Tie-break order (§11)** — higher reputation → higher complaints → higher regulatory → higher price → higher distance score (closer office) → higher offices score → alphabetical by firm name.

**Ingestion** — every numeric input to the ranker is pre-computed in the Master Export workbook and loaded by `scripts/import_master_export.py` (one importer, six CSV tabs). The runtime ranker only consumes pre-processed numbers; there is no per-decision arithmetic at request time.

---

## Frontend

**Stack**: Next.js 15 App Router · TypeScript · Tailwind CSS · React Hook Form · Radix UI · Sonner

**Route groups**:

| Group | Routes | Description |
|---|---|---|
| `(marketing)` | `/`, `/how-it-works`, `/for-firms`, `/conveyancing`, `/contact`, `/privacy`, `/terms` | Public marketing with Navbar + Footer |
| `(public)` | `/chat`, `/results/[sessionId]`, `/review/[token]` | Consumer chat flow |
| `(firm)` | `/login`, `/enroll/[token]`, `/dashboard`, `/profile`, `/pricing`, `/reviews` | Authenticated firm portal |

**Key files**:

| File | Purpose |
|---|---|
| `lib/api.ts` | Typed fetch wrapper — all API calls go here |
| `lib/utils.ts` | `cn()`, `formatCurrency()`, token helpers |
| `lib/analytics.ts` | Meta Pixel + first-party `analytics_events` mirror; gated by consent |
| `lib/consent.ts` | Cookie-consent state (localStorage) read by Meta Pixel + analytics |
| `components/chat/ChatInterface.tsx` | Pathway-aware chat controller (Buying / Selling / Both) |
| `components/results/ResultsClient.tsx` | Ranked results table with per-row price-breakdown expander, reorder control, and complaints / regulatory cells |
| `components/results/ReorderControl.tsx` | Scorecard preference + include-distance toggle (re-issues `/api/public/search` with query params) |
| `components/results/ComplaintsCell.tsx`, `RegulatoryCell.tsx`, `SeverityCell.tsx` | Render the pre-computed star / display-text values from the summary tables |
| `components/results/AppointModal.tsx`, `CallbackModal.tsx` | Consent + contact-details capture for Proceed / Callback |
| `components/firm/FirmLayout.tsx` | Sidebar nav + auth wrapper |
| `components/firm/PriceCardForm.tsx` | Pricing CRUD form (post-pilot — pricing is currently driven from the Master Export workbook) |
| `components/CookieConsent.tsx` | Banner that writes consent state to localStorage |
| `components/MetaPixel.tsx`, `AnalyticsPageView.tsx` | Load `fbevents.js` after consent and fire PageView |
| `components/ReviewForm.tsx` | CML review submission (`/review/[token]`) |
| `next.config.ts` | API proxy rewrites, image domain allowlist |

**Conventions**:

- All interactive/stateful components are `"use client"`
- API calls always via `lib/api.ts` — never raw fetch in components
- `cn()` for conditional class merging (clsx + tailwind-merge)
- `toast.success()` / `toast.error()` via Sonner
- Forms via react-hook-form + Zod

**Tailwind tokens** — canonical palette per `docs/requirements.md` §4.1, defined in `frontend/tailwind.config.ts`:

| Token | Value | Usage |
|---|---|---|
| `teal` | `#0AE5F6` | Brand accent, gradient highlights |
| `navy` | `#080C64` | Headlines, footer, primary surfaces |
| `mint` | `#69E4B5` | Secondary accents, success states |
| `purple` | `#9747FF` | Gradient pairs with navy/teal |
| `brand-*` | indigo scale (`#3450e8` at 600) | Legacy primary — being phased out in Phase H |
| `.btn-primary`, `.btn-secondary`, `.btn-ghost` | — | Action button variants |
| `.card`, `.input`, `.label` | — | Form / surface primitives |

---

## Database

**Engine**: PostgreSQL 16 with UUID PKs, async driver (asyncpg)

**Data model**:

```
organisations
  ├─ offices (one-to-many, is_primary flag, office_type BRANCH/HO, lat/lng for distance)
  ├─ firm_users (one-to-many, roles: admin/staff)
  ├─ price_card (one-to-one, JSONB pricing, price_type enum)
  ├─ complaints_summary (one-to-one, pre-computed score + display text)
  ├─ regulatory_summary (one-to-one, pre-computed score + display text)
  ├─ appointments (via FK)
  └─ reviews (via FK, source: cml/google)

chat_sessions
  └─ appointments (one-to-many, FK nullable)
       └─ review_invitations (one-to-one)

analytics_events  (standalone — funnel + Meta Pixel mirror)
```

**Key table fields** — schema is aligned to the Master Export workbook (Firms / Reputation / Price / Complaints history / Regulatory history / Distance tabs). The `cml_firm_id` (e.g. `CML-001`) is the spreadsheet-owned identity; `sra_number` is preserved alongside as the regulator identity. Reputation, complaints and regulatory scores are pre-computed in the workbook.

`organisations` — `cml_firm_id` (UNIQUE), `sra_number` (UNIQUE), `name`, `trading_name`, `phone`, `referral_email`, `excluded` (binary eligibility — §8.13), `exclusion_reason`, `conveyancing_confirmed`, `transparency_statement_captured`, `enrolled`, `proceed_enabled`, `callback_enabled`, `active_in_pilot`, `enrollment_token`, `enrollment_token_used`, `google_rating`, `google_review_count`, `google_reviews_url`, `adjusted_reputation_value`, `master_export_updated_at`

`offices` — `org_id`, `address_line1`, `city`, `postcode`, `lat`, `lng`, `is_primary`, `office_type` (`BRANCH` / `HO`)

`firm_users` — `org_id`, `email`, `hashed_password`, `role` (admin/staff), `full_name`, `last_login`

`price_cards` — `org_id` (UNIQUE — one card per firm), `price_type` (`estimated` / `verified` / `no_data`), `pricing` (JSONB). Cards with `price_type='no_data'` are excluded from results at runtime.

`chat_sessions` — `practice_area` (`residential_conveyancing`), `answers` (JSONB — keyed by question id), `message_history` (JSONB), `results_cache` (JSONB — only the default `balanced` + auto-distance view is cached), `save_email`, `expires_at` (30 days). Scorecard preference and distance inclusion are **not** stored on the session — they're URL query params on `/api/public/search/{session_id}`.

`appointments` — `type` (appoint/callback), `status` (pending/confirmed/completed/cancelled), `client_name`, `client_email`, `client_phone`, `preferred_time`, `quoted_price`, `quote_breakdown`, `consent_contacted`, `consent_terms`, `firm_contact_made` (nullable bool — set by the consumer clicking Yes/No in either follow-up email), `conflict_check_outcome` (enum: `pending`/`clear`/`conflict`)

`complaints_summary` — one row per firm. `org_id` (UNIQUE), `score` (0–100, consumed directly by the ranker), `stars`, `display_text` (e.g. "Low" / "No published complaints history"), `decision_count_text`, `scale_context`, `issue_one`/`two`/`three`, `external_url` (LeO link), `last_updated`. Pre-computed in the Master Export from §6 tables.

`regulatory_summary` — one row per firm. `org_id` (UNIQUE), `score` (0–100), `stars`, `display_text`, `decision_count_text`, `outcome_one`/`two`/`three`, `external_url` (SRA link), `last_updated`. Pre-computed in the Master Export from §7.3 / §7.5 tables.

`reviews` — `source` (cml/google), `rating`, `text`, `reviewer_name`, `external_id`, `firm_response`, `firm_response_at`, `reported`, `reported_at`

`review_invitations` — `appointment_id`, `email`, `token`, `sent_at`, `used_at`, `expires_at`

`analytics_events` — `session_id`, `event_type`, `metadata` (JSONB), `created_at`. Mirrors Meta Pixel events for independent CSV export.

**Price card JSONB schema** (residential conveyancing — Master Export Price tab shape, Annex One §10):

```json
{
  "freehold": {
    "purchase": {"150000": 750, "250000": 900, "500000": 1000, "750000": 1100, "1000000": 1250, "1250000": 1350, "1500000": 1450},
    "sale":     {"150000": 750, "250000": 900, "500000": 1000, "750000": 1100, "1000000": 1250, "1250000": 1350, "1500000": 1450}
  },
  "leasehold": {
    "purchase": {"150000": 750, "250000": 900, "500000": 1000, "750000": 1100, "1000000": 1250, "1250000": 1350, "1500000": 1450},
    "sale":     {"150000": 750, "250000": 900, "500000": 1000, "750000": 1100, "1000000": 1250, "1250000": 1350, "1500000": 1450}
  },
  "modifiers": [
    {"name": "Purchase - New build (freehold)",          "amount":   0},
    {"name": "Purchase - New lease (leasehold)",         "amount":   0},
    {"name": "Purchase - Acting for lender",             "amount": 100},
    {"name": "Purchase - Shared ownership/Help to Buy",  "amount": 250},
    {"name": "Purchase - Gifted deposit",                "amount":  75},
    {"name": "Purchase - Unregistered title",            "amount": 150},
    {"name": "Sale - Unregistered title",                "amount": 150},
    {"name": "Sale - Additional mortgage redemption",    "amount": 100}
  ],
  "additional_costs": [
    {"name": "Additional - ID verification",     "amount":   8},
    {"name": "Additional - onboarding fee",      "amount":   0},
    {"name": "Additional - transfer admin fee",  "amount":  40},
    {"name": "SDLT admin fee",                   "amount":  80},
    {"name": "Leasehold admin fee",              "amount": 250}
  ],
  "disbursements": [
    {"name": "Disb - searches (CML standard pack)", "amount": 350}
  ]
}
```

**Total Effective Price** (per side of the matter — combined sales-and-purchase runs the pricer twice and sums):

```
P_estimated       = anchor_fee + Σ applicable modifiers + Σ applicable additional costs
P_legal_effective = P_estimated × (1 + c)   if price_type='estimated' (c = 0.075, §10)
                  = P_estimated             if price_type='verified'
P_effective       = P_legal_effective + (P_legal_effective × 0.20) + Σ disbursements (already inc. VAT)
```

`anchor_fee` is read from the matching `{tenure}.{side}` map by the user's purchase / sale price, snapping up to the nearest of the seven anchors (£150k / £250k / £500k / £750k / £1m / £1.25m / £1.5m). The Verified-price path uses Master Export amounts directly; the Estimated path applies the §10 confidence uplift `c = 0.075`. Cards with `price_type='no_data'` are excluded from results.

**Migrations**: Single Alembic file `alembic/versions/0001_initial_schema.py` covers all tables. Pre-launch the policy is to **edit `0001` in place and drop/recreate the dev DB**; no new Alembic revisions are added until go-live (see `scripts/wipe-and-reseed-railway-db.sh` for the Railway-side cycle).

---

## Local development

```bash
# Start all services (PostgreSQL, FastAPI, Next.js)
docker-compose up

# Run DB migrations (first time or after schema changes)
docker-compose exec backend alembic upgrade head
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/api/docs
- API health: http://localhost:8000/health

Copy `.env.example` → `.env` and fill in API keys before starting.

---

## Running tests

Tests require PostgreSQL running locally (`docker-compose up`). Run from the `backend/` directory:

```bash
# All tests
uv run pytest -v

# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests only
uv run pytest tests/integration/ -v

# Stop on first failure
uv run pytest -x -v

# Run a specific file
uv run pytest tests/integration/test_firm_pricing.py -v

# Run a specific test
uv run pytest tests/integration/test_firm_pricing.py::test_create_price_card_returns_201 -v
```

The test database (`test_cml_db`) is created and migrated automatically on the first run of each session, then truncated between each test. It requires PostgreSQL reachable at `localhost:5432`.

Install dev dependencies if not already done:

```bash
cd backend
uv sync --extra testing
```

---

## Firm onboarding

Four steps from Master Export data import to a logged-in firm user. For the pilot the founder curates pricing centrally in the workbook, so Steps 2–4 (firm-portal enrolment) are bypassed for most pilot firms — but the flow is wired up and supported.

---

### Step 1 — Import firm data from the Master Export workbook (one-off, repeatable)

Organisations enter the system via a single importer. No API involved. The Master Export workbook owns everything: firm identity, primary office, pricing, complaints / regulatory summaries, distance (additional offices), and reputation.

```bash
docker-compose exec backend python scripts/import_master_export.py \
  --input-dir scripts/seed_data/master_export

# Skip Fetchify postcode geocoding (no key set locally):
docker-compose exec backend python scripts/import_master_export.py \
  --input-dir scripts/seed_data/master_export --no-geocode

# Roll back inside a transaction (useful for verifying a workbook change):
docker-compose exec backend python scripts/import_master_export.py \
  --input-dir scripts/seed_data/master_export --dry-run
```

Expected CSVs in the `--input-dir` (one per workbook tab):
- `firms.csv` — one row per firm (Firms tab) → `organisations`, primary `offices` row
- `reputation.csv` — Reputation tab → `organisations.google_rating` / `_review_count` / `_reviews_url` / `adjusted_reputation_value`
- `complaints.csv` — Complaints history tab → `complaints_summary` (one row per firm)
- `regulatory.csv` — Regulatory history tab → `regulatory_summary` (one row per firm)
- `price.csv` — Price tab (two header rows) → `price_cards.pricing` JSONB + `price_type`
- `distance.csv` — Distance tab → additional `offices` rows (one per non-primary office)

The importer is idempotent: parents (organisations) are upserted by `cml_firm_id`; child collections (offices, price_card, summaries) are deleted and re-inserted on each run.

---

### Step 2 — Generate enrollment token (admin)

```
POST /api/admin/organisations/{org_id}/invite-enrollment
Headers: X-Admin-Key: <ADMIN_API_KEY>
```

Requirements: org must have `enrolled=false` and a `referral_email` set (from the Firms tab). All `/api/admin/*` routes require the `X-Admin-Key` header — it must match the `ADMIN_API_KEY` env var on the backend.

DB changes:
- `organisations.enrollment_token` → new UUID
- `organisations.enrollment_token_used` → false

Response:
```json
{
  "message": "Enrollment invitation sent to contact@firm.co.uk",
  "enrollment_token": "a1b2c3d4-..."
}
```

An invitation email is sent to `org.referral_email` with a link to `{APP_URL}/enroll/{token}`. If `SPARKPOST_API_KEY` is not set, the email is mocked (logged only) and the token is still returned in the response.

---

### Step 3 — Firm registers via enrollment token

Frontend: `/enroll/[token]`
API: `POST /api/firm/auth/register`

```json
{
  "enrollment_token": "a1b2c3d4-...",
  "email": "jane@firm.co.uk",
  "password": "SecurePass123",
  "full_name": "Jane Smith",
  "accept_terms": true
}
```

DB changes:
- `firm_users` row created with `role=admin`, bcrypt-hashed password
- `organisations.enrolled` → true
- `organisations.enrollment_token_used` → true

Response (201): JWT `access_token` + `org_id`, `user_id`, `email`, `role`.

---

### Step 4 — Firm logs in

Frontend: `/login`
API: `POST /api/firm/auth/login`

```json
{
  "email": "jane@firm.co.uk",
  "password": "SecurePass123"
}
```

DB changes:
- `firm_users.last_login` → current UTC timestamp

Response (200): same shape as register — JWT `access_token`.

JWT is stored in localStorage and sent as `Authorization: Bearer <token>` on all subsequent firm API calls (`/dashboard`, `/profile`, `/pricing`, `/reviews`).

---

### DB state summary

| Step | Table | Fields set |
|---|---|---|
| Import | `organisations` | `cml_firm_id`, `sra_number`, `name`, `trading_name`, `phone`, `referral_email`, `excluded`, `conveyancing_confirmed`, `transparency_statement_captured`, `enrolled`, `proceed_enabled`, `callback_enabled`, `active_in_pilot`, `google_rating`/`_review_count`/`_reviews_url`, `adjusted_reputation_value`, `master_export_updated_at` |
| Import | `offices` | `address_line1`, `city`, `postcode`, `is_primary`, `office_type`, optional `lat`/`lng` |
| Import | `price_cards` | `price_type`, `pricing` (JSONB) |
| Import | `complaints_summary` / `regulatory_summary` | `score`, `stars`, `display_text`, `issue_one..three` / `outcome_one..three`, `external_url` |
| Admin invite | `organisations` | `enrollment_token` (new UUID), `enrollment_token_used=false` |
| Register | `firm_users` | all fields, `role=admin` |
| Register | `organisations` | `enrolled=true`, `enrollment_token_used=true` |
| Login | `firm_users` | `last_login` |

---

## User actions & email workflow

After a consumer reaches the results page they can take one of two actions on
a top-5 contactable firm: **Proceed** (instruct) or **Request a Callback**.
The full pipeline below is what's wired up by Phase F.

### Action dispatch — Proceed and Callback

```
Results page
   │
   ├─ Proceed   → POST /api/public/appointments  type=appoint
   └─ Callback  → POST /api/public/appointments  type=callback
                       │
                       ▼
                FastAPI handler:
                  • validate consent flags (400 if false)
                  • verify org enrolled (404 otherwise)
                  • insert into `appointments`
                  • dispatch two emails via BackgroundTasks
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
      User-facing copy       Firm-facing email
      (CML from-line)        (sent in user's name)
```

**Emails dispatched per action** — handler in `app/api/public/appointments.py`
branches on `body.type`:

| Action | User copy (`send_*_user_copy`) | Firm email (`send_*_to_firm`) |
|---|---|---|
| Proceed | Confirms instruction; reminds about excluded disbursements (Stamp Duty, indemnity policies, …) with link to `/disbursements` | "Conveyancing instruction from {client_name} via Choose My Lawyer" |
| Callback | Confirms the availability window passed to the firm | "Callback request from {client_name} via Choose My Lawyer" |

### "Sent in the user's name" mechanic

The firm-facing email is the consumer talking to the firm — CML is the relay,
not the sender. `send_email()` in `app/services/email.py` accepts:

| kwarg | Wired to | Effect |
|---|---|---|
| `from_name` | client's display name | Firm sees the consumer's name in their inbox |
| `from_email` | (CML's verified domain) | Required by Sparkpost — the *envelope* sender is still us |
| `reply_to` | client's email | Hitting Reply in the firm's inbox goes straight to the consumer |
| `bcc` | `[settings.sparkpost_from_email]` | CML keeps an audit copy of every dispatched lead |

The CML BCC is silently dropped if `SPARKPOST_FROM_EMAIL` isn't configured
(local dev). Consumer copies don't override these — they go from CML's
default sender so the consumer sees "Choose My Lawyer" in their own inbox.

### Follow-up scheduler

Three APScheduler cron jobs fire from `app/tasks/followups.py`. Registered
into the shared scheduler by `register_followup_jobs()`, called from
`app/tasks/scheduler.py::start_scheduler` (which itself is wired into
the FastAPI lifespan in `app/main.py`). The scheduler used to also run a
weekly Google reviews sync; that job was retired when reputation data
moved into the Master Export workbook.

| Job | Cron (UTC) | Targets | Email | Sets |
|---|---|---|---|---|
| `_callback_followup_job` | daily 17:00 | Callbacks created today, `firm_contact_made IS NULL` | "Did the firm call you back?" with Yes / No links | `firm_contact_made` (via capture endpoint) |
| `_proceed_followup_job` | daily 09:00 | Proceeds created exactly 5 working days ago, `firm_contact_made IS NULL` | "Is your matter progressing?" + price-drift reminder + Yes / No links | `firm_contact_made` (via capture endpoint) |
| `_proceed_feedback_request_job` | daily 09:30 | Proceeds created `review_invitation_delay_days` (=60) days ago with no existing `review_invitations` row | "How was your experience with {firm_name}?" with `/review/{token}` link | inserts `review_invitations` row (UUID token, 30-day expiry) |

**Working days** — the 5-day Proceed job uses `working_days_ago(n, today)` to
walk back 5 weekdays only (Mon–Fri), so a Proceed made on a Friday gets its
follow-up the following Friday.

**Dedupe by date window** — none of these jobs need a `*_sent_at` column.
The query window is "appointments created in the 24-hour bucket of the
target date", so each appointment falls into exactly one daily cron run.
The 2-month job additionally LEFT JOINs `review_invitations` and filters
on `id IS NULL`, so a manual re-run can't double-issue review tokens.

The `_proceed_feedback_request_job` replaces the prior 90-day post-completion
review job. It keys off Proceed appointments at 60 days regardless of
`status`, which matches the conveyancing pilot's reality (matters run
8–12 weeks).

### One-click follow-up capture

The Yes / No buttons in the follow-up emails point at a public capture
endpoint guarded by HMAC tokens — there's no login involved.

```
Follow-up email
   │
   ├─ "Yes, they called"  → GET /api/public/appointments/{id}/firm-contact?answer=yes&token=<hmac>
   └─ "No, not yet"       → GET /api/public/appointments/{id}/firm-contact?answer=no&token=<hmac>
                                  │
                                  ▼
                        verify HMAC (settings.secret_key)
                                  │
                                  ▼
                        appointments.firm_contact_made = (answer == "yes")
                                  │
                                  ▼
                        renders a small HTML "Thanks" page
```

Token is `HMAC-SHA256(secret_key, "{appointment_id}:{yes|no}")` — generated
by `make_followup_token()`, verified by `verify_followup_token()` in
`app/services/followup_tokens.py`. A "yes" token won't validate against a
"no" link and vice-versa, so neither click can be forged from the other.

Token rejection paths:

| Condition | Response |
|---|---|
| `answer` not in `{yes, no}` | 400 |
| HMAC mismatch | 403 |
| Appointment not found | 404 |

### Admin conflict-check flow

When a firm replies to the Proceed email saying they can't act due to a
conflict of interest, an admin records it via:

```
POST /api/admin/appointments/{appointment_id}/conflict-check
Headers: X-Admin-Key: <ADMIN_API_KEY>
Body:    { "outcome": "clear" | "conflict" }
```

| `outcome` | Sets | Side effect |
|---|---|---|
| `clear` | `appointments.conflict_check_outcome = clear` | (none) |
| `conflict` | `appointments.conflict_check_outcome = conflict` | Emails the consumer with a deep link to `{APP_URL}/results/{session_id}` so they can pick another firm |

The email (`send_conflict_check_failed`) explicitly explains a conflict isn't
a reflection on the consumer — just an existing relationship the firm has
with another party. The deep link drops them straight back into their
ranked results so they don't re-do intake.

### Annex One traceability

| Plan ref | Implementation |
|---|---|
| §12.2 — Proceed / Callback emails sent "in the user's name" with CML BCC | `send_proceed_to_firm`, `send_callback_to_firm` set `from_name` + `reply_to` + `bcc` |
| §12.4 — Conflict-check failure emails the consumer with a link back to results | `POST /api/admin/appointments/{id}/conflict-check` with `outcome=conflict` |
| Email matrix — 5-WD Proceed follow-up, EOD Callback follow-up, 2-month feedback request | `_proceed_followup_job`, `_callback_followup_job`, `_proceed_feedback_request_job` |
| Excluded Disbursements reminder on consent | Modal copy in `AppointModal.tsx` / `CallbackModal.tsx`; mirrored in Proceed user-copy email |

---

## Deployment (Railway)

**Services**: Two separate Railway services — `backend` and `frontend` — each built from their respective Dockerfiles. PostgreSQL is a Railway managed database add-on.

**Service config** (`railway.toml` in each directory):

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/health"   # backend; "/" for frontend
healthcheckTimeout = 120
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

**Backend Dockerfile notes**:
- Python 3.12-slim base
- Uses `uv` for dependency resolution, exports to `requirements.txt`, installs via pip (avoids uv in prod)
- `start.sh` runs Alembic migrations then starts Uvicorn
- PORT env var injected by Railway: `uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"`

**Frontend Dockerfile notes**:
- Multi-stage build: deps → builder → runner (node:20-alpine)
- `NEXT_PUBLIC_*` vars are baked in at `next build` — they must be passed as Docker build args via Railway "build variables", not runtime env vars
- `npm ci` (not `npm install`) to use lockfile for reproducible builds

### Environment variables

Set in the Railway dashboard per service. Anything marked **required** will leave a feature broken (or the service refusing to start) if absent.

**Backend** (runtime env):

| Variable | Required? | Purpose |
|---|---|---|
| `DATABASE_URL` | ✅ | Railway PG addon reference; `postgresql://` is auto-converted to `postgresql+asyncpg://` by `config.py` |
| `SECRET_KEY` | ✅ | JWT signing + HMAC follow-up tokens. Random 32+ chars. |
| `ADMIN_API_KEY` | ✅ | Header value for `/api/admin/*` (`X-Admin-Key`). Must be non-empty or every admin route 401s. |
| `ENVIRONMENT` | ✅ | `production` — enables HSTS in the security-headers middleware (`app/main.py`) |
| `APP_URL` | ✅ | Frontend public URL (e.g. `https://choosemylawyer.co.uk`). Used in email links, save-for-later URLs, conflict-check deep links. |
| `API_URL` | ✅ | Backend public URL. Currently logged on startup; reserve for future use. |
| `CORS_ORIGINS` | ✅ | Comma-separated. Must include both the Railway subdomain and the production custom domain during cutover (e.g. `https://cml-frontend.up.railway.app,https://choosemylawyer.co.uk,https://www.choosemylawyer.co.uk`) |
| `SPARKPOST_API_KEY` | ✅ for emails | Without this, every email path silently no-ops (logged only) |
| `SPARKPOST_FROM_EMAIL` | ✅ for emails | Must match a verified Sparkpost sending domain. Also receives the BCC of every Proceed/Callback firm email. |
| `SPARKPOST_FROM_NAME` | optional | Default `Choose My Lawyer` |
| `GOOGLE_PLACES_API_KEY` | unused (legacy) | Read by `config.py` for backwards-compatibility but no longer consumed — reputation now arrives pre-baked from the Master Export workbook (`adjusted_reputation_value`). Safe to omit. |
| `FETCHIFY_API_KEY` | optional | Postcode → lat/lng. Without it the distance factor falls back to no distance score; the rest of ranking still works |
| `JWT_ALGORITHM`, `JWT_EXPIRY_HOURS` | optional | Defaults `HS256`, `24` |
| `REVIEW_INVITATION_DELAY_DAYS`, `REVIEW_INVITATION_EXPIRY_DAYS` | optional | Defaults `60`, `30` (Phase F) |
| `PROCEED_FOLLOWUP_WORKING_DAYS` | optional | Default `5` |
| `EXCLUDED_DISBURSEMENTS_URL` | optional | Default `https://choosemylawyer.co.uk/disbursements` (linked from Proceed user-copy email) |
| `RATE_LIMIT_PUBLIC`, `RATE_LIMIT_LOGIN` | optional | Defaults `100`, `5` (per-IP, per-minute) |

**Frontend** (build args + minimal runtime):

| Variable | Where set | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Railway **build variable** | Backend public URL. Baked into the browser bundle by `next build` — runtime-only env will not work. |
| `NEXT_PUBLIC_META_PIXEL_ID` | Railway **build variable** | Meta Pixel ID. Without this the `<MetaPixel />` component renders nothing and Meta tracking is silently disabled even if consent is granted. |

### Cloudflare DNS

Production domain: `choosemylawyer.co.uk`. Proxied through Cloudflare; Railway terminates TLS upstream so set Cloudflare to **Full (strict)** SSL mode.

| Type | Name | Target | Notes |
|---|---|---|---|
| CNAME | `@` (apex) or `choosemylawyer.co.uk` | Railway frontend public URL | Cloudflare CNAME flattening lets you CNAME the apex |
| CNAME | `www` | Same as apex | Redirect to apex via Cloudflare page rule, or serve directly |
| CNAME | `api` | Railway backend public URL | Backend service domain. Add `https://api.choosemylawyer.co.uk` to backend `CORS_ORIGINS` is **not** needed (it's the API itself); but `NEXT_PUBLIC_API_URL` should point here. |
| TXT | `@` | Sparkpost SPF (`v=spf1 include:sparkpostmail.com ~all`) | From Sparkpost dashboard |
| TXT | `scph0125._domainkey` (or similar) | Sparkpost DKIM record | From Sparkpost dashboard — the selector name comes from your Sparkpost setup |
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:postmaster@choosemylawyer.co.uk` | Start with `p=none` for monitoring; tighten later |

After DNS resolves, in Railway add custom domains to each service (frontend gets `choosemylawyer.co.uk` + `www`; backend gets `api`). Railway issues TLS certs automatically.

### Go-live checklist

- [ ] Railway PG addon provisioned; `DATABASE_URL` reference set on backend service
- [ ] All **required** backend env vars set (table above); deploy is green
- [ ] `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_META_PIXEL_ID` set as Railway **build** variables on the frontend service; rebuild has run (not just redeploy)
- [ ] `CORS_ORIGINS` includes the production domain(s)
- [ ] Sparkpost sending domain verified; SPF/DKIM/DMARC records propagated
- [ ] First deploy: `alembic upgrade head` ran cleanly (logged in `start.sh` output)
- [ ] Ops data bootstrap done — see "Ops data bootstrap" below; final `import_master_export.py` run reports the expected row counts for `organisations`, `offices`, `price_cards`, `complaints_summary`, `regulatory_summary`
- [ ] `scripts/smoke_test.py --base-url https://api.choosemylawyer.co.uk --admin-key $ADMIN_API_KEY` passes against production
- [ ] Cookie consent banner appears in incognito on `https://choosemylawyer.co.uk`; rejecting hides it; accepting loads `fbevents.js`
- [ ] Meta Events Manager test-events viewer shows live PageView + IntakeStarted while clicking through
- [ ] Manual Proceed click confirms firm receives email **from the user's name** (display name + reply-to), CML BCC arrives in `SPARKPOST_FROM_EMAIL` inbox
- [ ] HSTS header present on backend response (`curl -I https://api.choosemylawyer.co.uk/health` shows `Strict-Transport-Security`)

---

## Ops data bootstrap

The Railway DB starts empty. The seed dataset under `backend/scripts/seed_data/master_export/` is the six-CSV export of the Master Export workbook — the same shape the importer will consume against real data — and it's the only path into the ops environment. There is no separate "demo" code path, no synthetic-data generator, and no per-feed importer.

### 1. Load into the ops DB

A single command imports all six CSVs:

```bash
docker-compose exec backend python scripts/import_master_export.py \
  --input-dir scripts/seed_data/master_export
```

Useful flags:

| Flag | Effect |
|---|---|
| `--no-geocode` | Skip Fetchify postcode geocoding — distance scoring will fall back to no-distance, the rest of ranking still works |
| `--dry-run` | Run inside a transaction and roll back — useful for verifying a workbook change before persisting |

The importer is idempotent. Parents (`organisations`) are upserted by `cml_firm_id`; child collections (`offices`, `price_card`, `complaints_summary`, `regulatory_summary`) are deleted and re-inserted on every run, so re-running cleanly reflects any spreadsheet edits.

#### Running against Railway from your laptop

The Railway CLI's `railway shell` **does not SSH into a container** — it opens a local subshell with Railway env vars exported. That means:

- The script runs on your laptop, using your project's local Python venv (so use `uv run python …` from the `backend/` directory).
- `DATABASE_URL` is exported pointing at Railway's **internal** Postgres hostname (`postgres.railway.internal`), which is unreachable from outside Railway's network. You must override it with the **public** TCP-proxy URL for the duration of the import.

Two safe ways to get the public URL:

```bash
# CLI:
railway variables --service Postgres | grep -i DATABASE_PUBLIC_URL

# Or dashboard: Postgres service → Variables tab → DATABASE_PUBLIC_URL
# (or Connect tab → Public Network)
```

It looks like `postgresql://postgres:<password>@<host>.proxy.rlwy.net:<port>/railway` — **must** start with `postgresql://` or `postgres://`; SQLAlchemy rejects URLs without a scheme.

Full procedure:

```bash
# 1. Open a Railway subshell (this exports env vars locally — internal DATABASE_URL):
cd backend
railway shell

# 2. Override DATABASE_URL with the public proxy URL for laptop access:
export DATABASE_URL="postgresql://postgres:<password>@<host>.proxy.rlwy.net:<port>/railway"

# 3. Sanity-check the override:
echo "${DATABASE_URL:0:30}…"
# Should print "postgresql://postgres:…@<host>.proxy.rlwy.net" — NOT "postgres.railway.internal"

# 4. Run the importer via the local venv:
uv run python scripts/import_master_export.py \
  --input-dir scripts/seed_data/master_export --no-geocode

# 5. Exit the subshell so DATABASE_URL drops back to your local dev value:
exit
```

⚠ **Never overwrite the backend service's `DATABASE_URL` in Railway** — it must stay the internal hostname so the deployed service uses the private network (faster, free intra-region traffic). The override above is local-shell-only.

**Pricing source of truth.** The MVP has no admin pricing form — every WMCA firm is priced by the founder in the Master Export workbook. Annex One §3 requires the full market to be ranked, so all firms get a price card; the search service then filters on `enrolled=true AND active_in_pilot=true` to extract the top-5 contactable. The firm-portal `/enroll/{token}` flow exists but is bypassed for the pilot — the spreadsheet is canonical. To onboard a real firm: edit `firms.csv` (`Signed up? = TRUE`, plus the corresponding flags) and `price.csv` (`Price type` = `Verified` once you have a transparency statement on file), then re-run `import_master_export.py`.

### 2. End-to-end smoke test

Once the dataset is loaded, drive the system through a full user journey to confirm everything works. Unlike the importer, the smoke test only needs to reach the backend's **public HTTP API** — it never connects directly to the database, so no `DATABASE_URL` override is needed.

Locally against docker-compose:

```bash
docker-compose exec backend python scripts/smoke_test.py \
  --admin-key "$ADMIN_API_KEY"
```

Against Railway from your laptop (requires `ADMIN_API_KEY` to be set in the Railway dashboard first — see "Environment variables" above):

```bash
cd backend
railway shell
uv run python scripts/smoke_test.py \
  --base-url https://api.choosemylawyer.co.uk \
  --admin-key "$ADMIN_API_KEY"
exit
```

The script exercises health, session creation, the full intake, balanced + a prioritised scorecard view, the §8.13 `excluded` filter, complaints + regulatory source-URL rendering, Proceed appointment, admin conflict-check, analytics event capture and admin CSV export — and exits non-zero on any failure. Manual checks the script *can't* automate are listed in PLAN.md "Verification" (Sparkpost inbox confirmation that firm emails arrive in the user's name, Meta Events Manager test-events viewer, browser cookie banner UX).

### 3. Replacing the seed dataset with the live workbook

When the live Master Export workbook is ready, drop its six CSV exports into `backend/scripts/seed_data/master_export/` (overwriting the committed seed files) and re-run the importer. Because every parent is upserted by `cml_firm_id` and every child collection is wiped + reinserted, the same command does both "first load" and "reflect every spreadsheet change since":

```bash
docker-compose exec backend python scripts/import_master_export.py \
  --input-dir scripts/seed_data/master_export
```

The seed dataset uses CML firm IDs `CML-001 .. CML-015` and real SRA numbers / firm names from the WMCA. There is no "synthetic-only" prefix to delete — the importer is the authority on what should be present, so simply replacing the CSVs is enough.

### 4. Wipe and reseed Railway (one command)

For the pre-launch workflow where `0001_initial_schema.py` is edited in place, deploys leave the prod DB on a stale schema until it's dropped and recreated. `scripts/wipe-and-reseed-railway-db.sh` does the full cycle against the **currently linked** Railway project + environment.

First-time setup on a new machine — log into Railway and link the project so the CLI knows which workspace + project to target:

```bash
railway login                                     # opens browser, one-time
railway link --project cml                        # link this repo to the cml project
railway environment production                    # target prod (or staging)
railway status                                    # sanity-check: project=cml, env=production
```

Then run the script from the repo root:

```bash
scripts/wipe-and-reseed-railway-db.sh --dry-run   # show what'll be targeted
scripts/wipe-and-reseed-railway-db.sh             # prompts for 'WIPE'
scripts/wipe-and-reseed-railway-db.sh --yes       # CI / unattended
```

The script:
1. Auto-detects the Postgres service (any name matching `^postgres`, override with `--service NAME`).
2. Pulls `DATABASE_PUBLIC_URL` from that service via `railway variable list --json` — never echoed.
3. Confirms the target host, requires you to type `WIPE` (unless `--yes`).
4. `DROP SCHEMA public CASCADE; CREATE SCHEMA public;` via local `psql`.
5. `uv run alembic upgrade head` in `backend/`.
6. `uv run python scripts/import_master_export.py --input-dir scripts/seed_data/master_export --no-geocode`.
7. Prints row counts for `organisations`, `offices`, `price_cards`, `complaints_summary`, `regulatory_summary` so you can eyeball seeding worked.

Prereqs: `railway`, `psql` (from `libpq`), `jq`, `uv`. The script bails early if any are missing.

To target a different environment, switch context first — `railway environment staging` — then re-run. There's no `--environment` flag, by design: it forces a `railway status` glance before destruction.

⚠ **Destructive — pre-launch only.** Erases every chat session, appointment, review, and firm user. Do not run after 1 June 2026 without a `pg_dump` first.

---

## Lessons Learned

1. **`NEXT_PUBLIC_*` vars are build-time** — they must be available at `docker build` / `next build` time. Railway supports "build variables" (set in service settings) to pass them into the Dockerfile via `ARG` + `ENV`. Setting them only as runtime env vars will result in `undefined` in the browser bundle.

2. **Railway injects `PORT`** — don't hardcode 8000 in the Dockerfile CMD. Use `${PORT:-8000}` to respect Railway's dynamic port assignment.

3. **Database URL protocol** — Railway PostgreSQL connection strings use `postgresql://` but asyncpg requires `postgresql+asyncpg://`. The `config.py` validator handles this conversion automatically.

4. **Alembic runs on every deploy** — `start.sh` runs `alembic upgrade head` before Uvicorn starts. This is safe (idempotent) and ensures migrations are always applied. On the first deploy it creates all tables.

5. **CORS must include both Railway subdomain and custom domain** — set `CORS_ORIGINS` to a comma-separated list before DNS cutover, e.g. `https://cml-frontend.up.railway.app,https://choosemylawyer.co.uk`.

6. **Volume mounts only for local dev** — `docker-compose.yml` mounts source code for hot reload. The production Dockerfiles copy source at build time; do not carry over dev volume patterns.

7. **uv in prod** — the backend Dockerfile uses uv to generate a `requirements.txt` then installs via pip. This avoids shipping uv itself into the final image and keeps the layer cache stable.

8. **Health checks** — Railway uses the `healthcheckPath` to verify the service is up before routing traffic. Backend exposes `GET /health`; frontend relies on `/` returning 200. Without this, Railway can route to the service before it's ready.

---

## DB access

```bash
docker-compose exec db psql -U cml -d cml_db
```
