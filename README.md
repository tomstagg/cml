# Choose My Lawyer

UK legal comparison platform. The **MVP pilot** is scoped to **residential conveyancing** in the **West Midlands Combined Authority** (go-live 1 June 2026, ~90-day PPC-driven pilot). Consumers answer a 13-step guided chat and receive a ranked list of solicitors with calculated Total Effective Prices. Firms enrol, configure pricing, and receive Proceed / Callback requests via the platform. Admin manages enrolment and Google review sync.

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
| `app/tasks/review_sync.py` | APScheduler entrypoint + weekly Google reviews sync |
| `app/tasks/followups.py` | Phase F follow-up jobs (callback EOD, 5-WD Proceed, 2-month feedback) |

**API namespaces**:

- `GET/POST /api/public/*` — unauthenticated (chat, search, appointments, reviews)
- `POST/GET/PATCH /api/firm/*` — JWT Bearer (firm dashboard, pricing, reviews)
- `GET/POST /api/admin/*` — internal only; every route requires the `X-Admin-Key` header (env var `ADMIN_API_KEY`)

**Services**:

| Service | Purpose |
|---|---|
| `auth.py` | bcrypt hashing, JWT sign/verify (24hr expiry) |
| `chat.py` | 13-question conveyancing intake engine + intake flag normalisation |
| `price_calc.py` | Total Effective Price calculation from JSONB pricing + intake flags |
| `ranking.py` | Pure factor scorers (Annex One §5–9): reputation, price, complaints, regulatory, distance, offices |
| `scorecard.py` | Weight tables (balanced + 6 prioritised) and tie-broken `apply()` (Annex One §11, §16) |
| `search.py` | Full-market 6-factor ranking + top-5 contactable extraction (Annex One §3.5) |
| `geocoding.py` | Fetchify.io postcode → lat/lng |
| `email.py` | Sparkpost transactional emails (mocked if no key); Proceed/Callback senders dispatch in the user's name with `reply_to` + CML BCC |
| `followup_tokens.py` | HMAC-signed yes/no tokens for one-click follow-up replies |
| `reviews.py` | Google Places sync, aggregate rating calculation |

**Ranking algorithm** — deterministic six-factor scorecard (Annex One §5–11). Each factor is scored 0–100 at full numerical precision; the overall score is a weighted sum and only the displayed integer is rounded.

| Factor | Source data | Score basis | Balanced weight |
|---|---|---|---|
| Reputation | `aggregate_rating`, `aggregate_review_count` | `ARV = rating × (1 + 0.025 × ln(reviews + 1))`, min–max normalised across results set | 25% |
| Price | active conveyancing `price_card` → Total Effective Price | `(P_max − P) / (P_max − P_min) × 100` (lower price → higher score) | 25% |
| Complaints | `complaints_decisions` (LeO) | `100 − Σ ((severity_score × remedy_amount_score) + handling_penalty)` | 15% |
| Regulatory | `regulatory_decisions` (SRA + SDT) | `100 − Σ deductions` per §7.3 / §7.5 tables (no floor — can go negative) | 15% |
| Distance | `offices.lat/lng` vs property postcode | min–max normalised (closer → higher); user can opt out | 10% |
| Offices | `count(offices)` | banded: 1→70, 2–3→78, 4–6→85, 7–10→90, 11–20→95, 21+→100 | 10% |

**Prioritised scorecard** — the user can pick one priority factor on the chat preference step. That factor's weight becomes 40; the other five share 60 in their balanced-scorecard ratios (e.g. Reputation Priority: rep 40, price 20, complaints 12, regulatory 12, distance 8, offices 8). The seven weight sets are pinned verbatim from Annex One §16.6 in `scorecard.py::SCORECARDS`.

**Distance excluded (§8.2)** — if the user opts out of distance, its weight goes to 0 and the remaining factors are proportionately rescaled so the sum stays at 100.

**Sequencing rule (§3.5)** — the *entire* in-scope WMCA market is ranked first using the chosen scorecard. The top-5 contactable firms are then extracted from that ordering by filtering on `enrolled=true`. Enrolled firms are never ranked separately — this preserves the "whole of market / fully independent" positioning.

**Eligibility filter (§8.13)** — firms with `organisations.intervened=true` (an SRA Intervention) are removed from results entirely before ranking.

**Tie-break order (§11)** — higher reputation → higher complaints → higher regulatory → higher price → higher distance score (closer office) → higher offices score → alphabetical by firm name.

**Ingestion** — all LeO and SRA decision data is normalised at ingest into structured deduction values (`scripts/import_leo_csv.py`, `scripts/import_sra_decisions_csv.py`) so the runtime ranker only consumes pre-processed numbers.

CML reviews are weighted 2× vs Google reviews in the aggregate rating consumed by the reputation factor.

---

## Frontend

**Stack**: Next.js 15 App Router · TypeScript · Tailwind CSS · React Hook Form · Radix UI · Sonner

**Route groups**:

| Group | Routes | Description |
|---|---|---|
| `(marketing)` | `/`, `/how-it-works`, `/for-firms`, `/contact`, `/privacy`, `/terms` (legacy `/probate` page slated for replacement by `/conveyancing` in Phase H) | Public marketing with Navbar + Footer |
| `(public)` | `/chat`, `/results/[sessionId]`, `/review/[token]` | Consumer chat flow |
| `(firm)` | `/login`, `/enroll/[token]`, `/dashboard`, `/profile`, `/pricing`, `/reviews` | Authenticated firm portal |

**Key files**:

| File | Purpose |
|---|---|
| `lib/api.ts` | Typed fetch wrapper — all API calls go here |
| `lib/utils.ts` | `cn()`, `formatCurrency()`, token helpers |
| `components/chat/ChatInterface.tsx` | 13-step chat controller |
| `components/results/ResultsClient.tsx` | Ranked results with sort/filter |
| `components/firm/FirmLayout.tsx` | Sidebar nav + auth wrapper |
| `components/firm/PriceCardForm.tsx` | Pricing CRUD form |
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
  ├─ offices (one-to-many, is_primary flag, lat/lng for distance)
  ├─ firm_users (one-to-many, roles: admin/staff)
  ├─ price_cards (one-to-many, JSONB pricing, active flag)
  ├─ complaints_decisions (one-to-many, LeO — Annex One §6)
  ├─ regulatory_decisions (one-to-many, SRA + SDT — Annex One §7)
  ├─ appointments (via FK)
  └─ reviews (via FK, source: cml/google)

chat_sessions
  └─ appointments (one-to-many, FK nullable)
       └─ review_invitations (one-to-one)

analytics_events  (standalone — funnel + Meta Pixel mirror, Phase I)
```

**Key table fields**:

`organisations` — `sra_number`, `name`, `auth_status`, `enrolled`, `enrollment_token`, `intervened` (binary eligibility — §8.13), `google_place_id`, `aggregate_rating`, `aggregate_review_count`

`offices` — `org_id`, `postcode`, `lat`, `lng`, `is_primary`

`firm_users` — `org_id`, `email`, `hashed_password`, `role` (admin/staff), `last_login`

`price_cards` — `org_id`, `practice_area` (`residential_conveyancing`), `pricing` (JSONB), `active`

`chat_sessions` — `answers` (JSONB), `message_history` (JSONB), `results_cache` (JSONB), `scorecard_preference` (enum: `balanced`/`reputation`/`price`/`complaints`/`regulatory`/`distance`/`offices`), `include_distance` (bool), `expires_at` (30 days)

`appointments` — `type` (appoint/callback), `status` (pending/confirmed/completed/cancelled), `client_name`, `client_email`, `quoted_price`, `quote_breakdown`, `firm_contact_made` (nullable bool — set by the consumer clicking Yes/No in either follow-up email), `conflict_check_outcome` (enum: `pending`/`clear`/`conflict`), consent fields

`complaints_decisions` — `org_id`, `decision_id` (LeO ID), `decision_date`, `remedy_type`, `severity_band`, `severity_score`, `remedy_amount`, `remedy_amount_score`, `complaint_handling_penalty`, `source_url`. Pre-computed at ingest from §6 tables.

`regulatory_decisions` — `org_id`, `source` (`sra`/`sdt`), `decision_id`, `decision_date`, `decision_type` (rebuke/fine_band_a..d/control_order/disqualification/strike_off/intervention), `deduction`, `sdt_fine_amount`, `source_url`. Pre-computed at ingest from §7.3 / §7.5 tables.

`analytics_events` — `session_id`, `event_type`, `metadata` (JSONB), `created_at`. Mirrors Meta Pixel events for independent CSV export.

`reviews` — `source` (cml/google), `rating`, `text`, `external_id`, `firm_response`, `reported`

`review_invitations` — `appointment_id`, `token`, `sent_at`, `used_at`, `expires_at`

**Price card JSONB schema** (residential conveyancing, Quoted Prices only this pilot — Annex One §10):

```json
{
  "practice_area": "residential_conveyancing",
  "matter_types": ["purchase", "sale", "purchase_and_sale", "remortgage"],
  "pricing_model": "band",
  "bands": [
    {"purchase_price_min": 0, "purchase_price_max": 250000, "fee": 950},
    {"purchase_price_min": 250000, "purchase_price_max": 500000, "fee": 1250},
    {"purchase_price_min": 500000, "purchase_price_max": null, "fee": 1750}
  ],
  "adjustments": [
    {"name": "Leasehold supplement",       "amount": 250, "condition": "tenure==leasehold"},
    {"name": "New build supplement",       "amount": 200, "condition": "new_build==true"},
    {"name": "Help to Buy ISA admin",      "amount":  75, "condition": "help_to_buy_isa==true"},
    {"name": "Shared ownership supplement","amount": 250, "condition": "shared_ownership==true"},
    {"name": "Mortgage handling",          "amount": 150, "condition": "mortgage==true"}
  ],
  "included_disbursements": [
    {"name": "Local authority search",         "amount": 180, "vat_applies": true},
    {"name": "Drainage & water search",        "amount":  65, "vat_applies": true},
    {"name": "Bankruptcy search",              "amount":   6, "vat_applies": false},
    {"name": "Land Registry registration fee", "amount": 150, "vat_applies": false}
  ],
  "excluded_disbursements_note": "Stamp Duty Land Tax, leasehold notice fees, …",
  "vat_applies_to_fees": true
}
```

**Total Effective Price** = base fee (band lookup by `purchase_price`) + matching adjustments + VAT on legal fees + Σ included disbursements (with each item's VAT applied per `vat_applies`). The Estimated Price path and confidence factors `c`/`d` are deferred post-pilot.

**Migrations**: Single Alembic file `alembic/versions/0001_initial_schema.py` covers all tables.

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

Four steps from SRA data import to a logged-in firm user.

---

### Step 1 — Import SRA data (one-off)

Organisations enter the system via CSV import. No API involved. For the WMCA pilot, run with the West Midlands postcode-prefix filter:

```bash
docker-compose exec backend python scripts/import_sra_csv.py \
  --csv /path/to/sra_firms.csv --region "West Midlands" --geocode
```

DB result:
- `organisations` row: `enrolled=false`, `enrollment_token=null`
- `offices` row: primary office with postcode (+ lat/lng if `--geocode`)

The same import pattern is also used for the two pre-runtime data feeds the ranker depends on (Annex One §6–7 mandates that all interpretation, cleansing and scoring of LeO / SRA data is completed *before* runtime):

```bash
# Legal Ombudsman complaints decisions → complaints_decisions
docker-compose exec backend python scripts/import_leo_csv.py --csv /path/to/leo_decisions.csv

# SRA + SDT regulatory decisions → regulatory_decisions (interventions flip
# organisations.intervened=true and are not added as scored rows)
docker-compose exec backend python scripts/import_sra_decisions_csv.py --csv /path/to/decisions.csv
```

For local/smoke testing, insert directly:

```bash
docker-compose exec db psql -U cml -d cml_db -c "
INSERT INTO organisations (id, sra_number, name, auth_status, enrolled, enrollment_token_used, email)
VALUES (gen_random_uuid(), 'SRA123458', 'Test Law Firm Ltd', 'authorised', false, false, 'tom@gmail.com');
"
```

---

### Step 2 — Generate enrollment token (admin)

```
POST /api/admin/organisations/{org_id}/invite-enrollment
Headers: X-Admin-Key: <ADMIN_API_KEY>
```

Requirements: org must have `enrolled=false` and an `email` field set. All `/api/admin/*` routes require the `X-Admin-Key` header — it must match the `ADMIN_API_KEY` env var on the backend.

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

An invitation email is sent to `org.email` with a link to `{APP_URL}/enroll/{token}`. If `SPARKPOST_API_KEY` is not set, the email is mocked (logged only) and the token is still returned in the response.

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
| Import | `organisations` | `sra_number`, `name`, `auth_status`, `email`; `enrolled=false` |
| Import | `offices` | address, `postcode`, `is_primary=true`, optional `location` |
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
`app/tasks/review_sync.py::start_scheduler` (which itself is wired into
the FastAPI lifespan in `app/main.py`).

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
review job that lived in `tasks/review_sync.py`. The Phase F variant keys
off Proceed appointments at 60 days regardless of `status`, which matches
the conveyancing pilot's reality (matters run 8–12 weeks).

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
- `NEXT_PUBLIC_API_URL` must be set as a Railway build variable (not just runtime) — it's baked in at `next build`
- `npm ci` (not `npm install`) to use lockfile for reproducible builds

**Environment variables** — set in Railway dashboard per service:

Backend:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Railway provides as `postgresql://...` — config.py auto-converts to `asyncpg` |
| `SECRET_KEY` | Random 32+ char string for JWT signing |
| `ENVIRONMENT` | `production` |
| `APP_URL` | Frontend Railway domain (e.g. `https://cml-frontend.up.railway.app`) |
| `API_URL` | Backend Railway domain |
| `CORS_ORIGINS` | Comma-separated — include Railway domain + custom domain |
| `SPARKPOST_API_KEY` | Email |
| `GOOGLE_PLACES_API_KEY` | Review sync |
| `FETCHIFY_API_KEY` | Geocoding |

Frontend:

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend public URL — **build variable**, not runtime |

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
