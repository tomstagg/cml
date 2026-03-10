# Choose My Lawyer

UK legal comparison platform for probate — England & Wales MVP. Consumers answer a 13-step guided chat and receive ranked solicitor quotes. Firms enroll, configure pricing, and receive appointments via the platform. Admin manages enrollment and Google review sync.

See `PLAN.md` for architecture decisions and phase status, and `docs/cml-technical_scoping.pdf` for the full functional spec.

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
| `app/tasks/review_sync.py` | APScheduler jobs |

**API namespaces**:

- `GET/POST /api/public/*` — unauthenticated (chat, search, appointments, reviews)
- `POST/GET/PATCH /api/firm/*` — JWT Bearer (firm dashboard, pricing, reviews)
- `GET/POST /api/admin/*` — internal only (enroll firms, sync Google Places)

**Services**:

| Service | Purpose |
|---|---|
| `auth.py` | bcrypt hashing, JWT sign/verify (24hr expiry) |
| `chat.py` | 13-question probate flow engine, complexity flag extraction |
| `price_calc.py` | Quote calculation from JSONB pricing + complexity flags |
| `search.py` | Firm ranking — haversine distance, weighted score |
| `geocoding.py` | Fetchify.io postcode → lat/lng |
| `email.py` | Sparkpost transactional emails (mocked if no key) |
| `reviews.py` | Google Places sync, aggregate rating calculation |

**Ranking algorithm** (weights shift per `ranking_preference` answer):

```
score = price_score * 0.60 + reputation_score * 0.25 + distance_score * 0.15
```

CML reviews are weighted 2× vs Google reviews in the aggregate rating.

---

## Frontend

**Stack**: Next.js 15 App Router · TypeScript · Tailwind CSS · React Hook Form · Radix UI · Sonner

**Route groups**:

| Group | Routes | Description |
|---|---|---|
| `(marketing)` | `/`, `/probate`, `/how-it-works`, `/for-firms`, `/contact`, `/privacy`, `/terms` | Public marketing with Navbar + Footer |
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

**Tailwind tokens**:

| Token | Usage |
|---|---|
| `brand-600` (#0d9488) | Primary CTAs, active states |
| `.btn-primary` | Primary action button |
| `.btn-secondary` | Outline button |
| `.card` | White rounded card with border |
| `.input` | Text input fields |

---

## Database

**Engine**: PostgreSQL 16 with UUID PKs, async driver (asyncpg)

**Data model**:

```
organisations
  ├─ offices (one-to-many, is_primary flag)
  ├─ firm_users (one-to-many, roles: admin/staff)
  ├─ price_cards (one-to-many, JSONB pricing, active flag)
  ├─ appointments (via FK)
  └─ reviews (via FK, source: cml/google)

chat_sessions
  └─ appointments (one-to-many, FK nullable)
       └─ review_invitations (one-to-one)
```

**Key table fields**:

`organisations` — `sra_number`, `name`, `auth_status`, `enrolled`, `enrollment_token`, `google_place_id`, `aggregate_rating`, `aggregate_review_count`

`offices` — `org_id`, `postcode`, `lat`, `lng`, `is_primary`

`firm_users` — `org_id`, `email`, `hashed_password`, `role` (admin/staff), `last_login`

`price_cards` — `org_id`, `practice_area`, `pricing` (JSONB), `active`

`chat_sessions` — `answers` (JSONB), `message_history` (JSONB), `results_cache` (JSONB), `expires_at` (30 days)

`appointments` — `type` (appoint/callback), `status` (pending/confirmed/completed/cancelled), `client_name`, `client_email`, `quoted_price`, `quote_breakdown`, consent fields

`reviews` — `source` (cml/google), `rating`, `text`, `external_id`, `firm_response`, `reported`

`review_invitations` — `appointment_id`, `token`, `sent_at`, `used_at`, `expires_at`

**Price card JSONB schema**:

```json
{
  "practice_area": "probate",
  "matter_types": ["grant_only", "full_administration"],
  "pricing_model": "fixed|band|percentage",
  "bands": [{"estate_value_min": 0, "estate_value_max": 325000, "fee": 1500}],
  "adjustments": [{"name": "IHT400", "amount": 500, "condition": "iht400"}],
  "disbursements": [{"name": "Probate Registry fee", "amount": 273, "estimated": false}],
  "vat_applies_to_fees": true
}
```

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

Organisations enter the system via CSV import. No API involved.

```bash
docker-compose exec backend python scripts/import_sra_csv.py \
  --csv /path/to/sra_firms.csv --region "London" --geocode
```

DB result:
- `organisations` row: `enrolled=false`, `enrollment_token=null`
- `offices` row: primary office with postcode (+ lat/lng if `--geocode`)

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
```

Requirements: org must have `enrolled=false` and an `email` field set.

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
