# CLAUDE.md — Choose My Lawyer (CML)

Guidance for Claude Code when working in this repository.

---

## Project overview

Choose My Lawyer is a UK legal comparison platform for England & Wales.
Consumers go through a guided probate chat flow and get a ranked list of solicitors with calculated quotes. Firms enroll, enter pricing, and receive appointments via the platform.

**MVP scope**: Probate only · England & Wales · Firms manually enrolled + priced.

Full functional spec: `docs/cml-technical_scoping.pdf`
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
# Start everything (PostgreSQL+PostGIS, FastAPI, Next.js)
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

**Stack**: FastAPI · SQLAlchemy (async) · Alembic · PostgreSQL + PostGIS · APScheduler

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

### Tailwind design system
| Token | Usage |
|---|---|
| `brand-600` (#0d9488) | Primary CTA buttons, active states |
| `brand-50` | Light backgrounds, chips |
| `.btn-primary` | Primary action buttons |
| `.btn-secondary` | Secondary/outline buttons |
| `.btn-ghost` | Subtle icon buttons |
| `.card` | White rounded card with border |
| `.input` | Text input fields |
| `.label` | Form labels |

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

```python
score = (
    price_score    * 0.60 +   # lower total cost = higher score
    reputation_score * 0.25 + # weighted avg (CML reviews 2x, Google 1x)
    distance_score  * 0.15    # closer = higher score
)
```

Weights shift based on `ranking_preference` answer in the chat (price/reputation/distance/balanced).

---

## Price card schema

Probate price cards are stored as JSONB. When editing the pricing logic, the canonical schema is in `app/schemas/firm.py` (`PriceCardData`) and the calculator is in `app/services/price_calc.py`.

```json
{
  "practice_area": "probate",
  "matter_types": ["grant_only", "full_administration"],
  "pricing_model": "band",
  "bands": [{"estate_value_min": 0, "estate_value_max": 325000, "fee": 1500}],
  "adjustments": [{"name": "IHT400", "amount": 500, "condition": "iht400"}],
  "disbursements": [{"name": "Probate Registry fee", "amount": 273, "estimated": false}],
  "vat_applies_to_fees": true
}
```

---

## Deferred (do not implement unless asked)

- Conveyancing practice area
- Additional UK regions
- AI price extraction
- Facebook / Trustpilot review aggregation
- Admin moderation UI
- Voice input
- Stripe / Xero billing
- Welsh language
