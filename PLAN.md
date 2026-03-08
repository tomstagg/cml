# Choose My Lawyer (CML) — Technical Architecture & Build Plan

## Context

"Choose My Lawyer" — a UK legal comparison platform for England & Wales.
Consumers go through a guided probate chat flow, and get a ranked list of solicitors
with calculated quotes (price, reputation, distance). Firms enroll, manually enter their
pricing, manage their profile, and receive appointments/callbacks via the platform.
Monetisation: free to start, referral fee (£125) later.

**MVP scope**: Probate only, single UK region, firms manually enrolled + priced.

Source of truth for functional spec: `docs/cml-technical_scoping.pdf`

---

## Key Simplifications vs SOZO Spec

| SOZO Spec | This Plan | Reason |
|---|---|---|
| GKE (Kubernetes) | Railway (PaaS) | Overkill for MVP; Railway is git-push simple |
| Celery + Redis | No Redis, APScheduler only | Not needed at low volume |
| Redis session cache | PostgreSQL sessions | Simpler; fine at tens of users |
| WordPress (Kinsta) | Next.js marketing pages | One codebase; add WordPress later |
| SRA API daily sync | Manual CSV upload script | No API integration needed for MVP |
| AI price scraping (Jina, Claude) | Manual firm pricing entry | Skip entirely for MVP |
| Prometheus + Grafana | Railway built-in metrics | Sufficient for MVP |
| Facebook + Trustpilot reviews | Google Places only | Fewer API approvals; Phase 2 |
| Google Reviews every 6h | Weekly cron | Cost saving on Places API |
| Conveyancing practice area | Probate only | Focus MVP on single area |
| Voice input | Not included | Phase 2 |

---

## Recommended Stack

### Application

| Layer | Technology | Why |
|---|---|---|
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS | SSR for SEO, fast to build, single codebase |
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), Alembic | Clean async API, Pydantic validation, auto docs |
| Database | PostgreSQL 16 | JSONB for price cards, lat/lng floats for distance |
| Background jobs | APScheduler (in-process with FastAPI) | Weekly Google Reviews sync; no Redis/Celery needed |
| Email | Sparkpost | Transactional templates, bounce handling |
| Reviews | Google Places API (weekly sync) | Firm reputation scores for ranking |
| Postcode | Fetchify.io | UK postcode → lat/lng for distance ranking |

### Infrastructure

| Component | Service | Monthly Cost (est.) |
|---|---|---|
| App hosting (all services) | Railway | ~£25-50/mo |
| Domain | Cloudflare Registrar | ~£10/yr |
| CDN + SSL + WAF | Cloudflare (free tier) | £0 |
| Email | Sparkpost (free to 500/mo) | £0 initially |
| Google Places API | Pay-per-use (weekly sync = very low) | ~£0-5/mo |

**Total running cost at MVP scale: ~£25-55/month**

---

## Architecture Overview

```
Browser
  │
  ├─ Next.js (SSR/CSR)
  │    ├─ Public: Marketing pages, probate chat, results, review form
  │    └─ Auth:   Firm dashboard (JWT HTTP-only cookie)
  │
  ▼
FastAPI Backend (REST API)
  ├─ /api/public/   — chat sessions, search, appointments, callbacks
  ├─ /api/firm/     — authenticated firm profile, pricing, appointments
  └─ APScheduler (in-process)
       └─ Weekly: Google Reviews sync → update reviews table
  │
  ▼
PostgreSQL
  ├─ organisations         (SRA firms — loaded via CSV upload script)
  ├─ offices               (locations with lat/lng floats for distance)
  ├─ price_cards           (manually entered by firms via dashboard)
  ├─ chat_sessions         (UUID, probate answers JSONB, expires 30 days)
  ├─ appointments          (appoint + callback records)
  ├─ reviews               (Google + CML native)
  └─ firm_users            (email, hashed_password, org_id)
```

### External Services
- **Fetchify.io** → consumer postcode → lat/lng for distance ranking
- **Google Places API** → weekly fetch of firm reviews + ratings
- **Sparkpost** → all transactional emails

---

## Data Model (Key Entities)

```sql
organisations
  id, sra_number, name, auth_status, website_url,
  enrolled BOOL, enrollment_token UUID, created_at

offices
  id, org_id FK, address, postcode,
  lat FLOAT, lng FLOAT        -- for Haversine distance queries

price_cards
  id, org_id FK, practice_area VARCHAR,
  pricing JSONB,              -- {model, bands, adjustments, disbursements}
  confidence FLOAT, active BOOL, updated_at

chat_sessions
  id UUID PK, practice_area VARCHAR,
  answers JSONB,              -- step-by-step probate answers
  message_history JSONB,
  results_cache JSONB,
  save_email VARCHAR,
  expires_at TIMESTAMPTZ, created_at

appointments
  id, session_id FK, org_id FK,
  type ENUM(appoint, callback),
  status ENUM(pending, confirmed, completed),
  client_name, client_email, client_phone,
  preferred_time VARCHAR, quoted_price DECIMAL,
  created_at

reviews
  id, org_id FK,
  source ENUM(cml, google),
  rating DECIMAL(2,1), text TEXT,
  reviewer_name, external_id VARCHAR,
  firm_response TEXT, firm_response_at,
  created_at, synced_at

review_invitations
  id UUID, appointment_id FK, email VARCHAR,
  token UUID UNIQUE, used_at, expires_at

firm_users
  id, org_id FK, email UNIQUE,
  hashed_password VARCHAR, role ENUM(admin, staff),
  created_at, last_login
```

### Price Card JSONB Schema (Probate)
```json
{
  "practice_area": "probate",
  "matter_types": ["grant_only", "full_administration"],
  "pricing_model": "fixed|band|percentage",
  "bands": [
    {"estate_value_min": 0, "estate_value_max": 325000,
     "fee": 1500, "currency": "GBP"}
  ],
  "adjustments": [
    {"name": "Taxable estate (IHT400)", "amount": 500}
  ],
  "disbursements": [
    {"name": "Probate Registry fee", "amount": 273, "estimated": false}
  ],
  "vat_applies_to_fees": true
}
```

---

## Ranking Algorithm

```python
# All scores normalised 0–1
score = (
    price_score * 0.60 +       # inverse of total cost (lower = better)
    reputation_score * 0.25 +  # weighted avg: CML reviews 2x, Google 1x
    distance_score * 0.15      # inverse of km from consumer postcode
)
```

- Top 5 enrolled firms: full display with Appoint / Request Callback buttons
- Position 6+: non-enrolled firms shown greyed, no action buttons

---

## Probate Chat Flow (13 Steps — as per spec)

Steps: service type → grant_only/full_admin → estate value → valid Will →
IHT400 → UK domiciled → UK properties count → bank accounts count →
investments count → overseas assets → beneficiaries count →
location preference → ranking preference

Consumer is anonymous (no account). Session stored by UUID in PostgreSQL,
persisted via unique URL for "save for later".

---

## Hosting (Railway)

Railway hosts everything in one project:
1. **FastAPI service** — Python web + background scheduler
2. **Next.js service** — frontend
3. **PostgreSQL plugin** — one-click, auto `DATABASE_URL` env var
4. (No Redis plugin needed)

Deployment: GitHub integration → push to `main` → auto-deploy.
Secrets/API keys in Railway dashboard environment variables.
Custom domain → Cloudflare DNS → Railway auto-issues SSL.

---

## Project Structure

```
cml/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── public/     # chat, search, appointments, reviews
│   │   │   ├── firm/       # dashboard (auth protected)
│   │   │   └── admin/      # org management, enrollment
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── auth.py           # JWT + bcrypt
│   │   │   ├── chat.py           # question flow engine (13 steps)
│   │   │   ├── price_calc.py     # price card → calculated quote
│   │   │   ├── search.py         # firm query + ranking
│   │   │   ├── email.py          # Sparkpost templates
│   │   │   ├── geocoding.py      # Fetchify postcode lookup
│   │   │   └── reviews.py        # Google sync + aggregation
│   │   ├── tasks/
│   │   │   └── review_sync.py    # APScheduler weekly job + review invitations
│   │   ├── config.py             # Pydantic settings
│   │   ├── database.py           # SQLAlchemy async engine + session
│   │   ├── dependencies.py       # FastAPI auth dependencies
│   │   └── main.py               # App entrypoint, middleware, router mounts
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 0001_initial_schema.py
│   ├── scripts/
│   │   └── import_sra_csv.py     # one-off CSV → organisations + offices
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx            # Root layout (Toaster)
│   │   ├── globals.css           # Tailwind + component classes
│   │   ├── not-found.tsx
│   │   ├── error.tsx
│   │   ├── (marketing)/          # Homepage, How It Works, For Firms, Probate, Contact, Privacy, Terms
│   │   ├── (public)/             # /chat, /results/[sessionId], /review/[token]
│   │   └── (firm)/               # /firm/login, /firm/enroll/[token], /firm/dashboard,
│   │                             #   /firm/profile, /firm/pricing, /firm/reviews
│   ├── components/
│   │   ├── ui/                   # Navbar, Footer
│   │   ├── chat/                 # ChatInterface, MessageBubble, OptionChips,
│   │   │                         #   PostcodeInput, ProgressBar, AnswerSidebar, SaveModal
│   │   ├── results/              # ResultsClient, FirmCard, AppointModal, CallbackModal
│   │   ├── firm/                 # FirmLayout, PriceCardForm
│   │   └── ReviewForm.tsx
│   ├── lib/
│   │   ├── api.ts                # Typed API client
│   │   └── utils.ts              # cn(), formatCurrency(), auth token helpers
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── Dockerfile
│
├── docs/
│   └── cml-technical_scoping.pdf
├── docker-compose.yml            # Local dev: PostgreSQL, FastAPI, Next.js
├── .env.example
└── PLAN.md                       # This file
```

---

## Task Breakdown & Status

### Phase 0 — Setup ✅
- [x] Monorepo init, git, `.env.example`
- [x] `docker-compose.yml` for local dev (PostgreSQL, FastAPI, Next.js)
- [x] FastAPI skeleton with health check endpoint
- [x] Next.js 15 skeleton with Tailwind CSS
- [x] Alembic configured, initial migration (all tables)

### Phase 1 — Data Foundation ✅
- [x] SQLAlchemy models for all entities (Organisation, Office, PriceCard, ChatSession, Appointment, Review, ReviewInvitation, FirmUser)
- [x] Alembic migration: create all tables
- [x] `scripts/import_sra_csv.py`: parse SRA CSV → insert organisations + offices

### Phase 2 — Firm Enrollment & Auth ✅
- [x] JWT auth: login, register via enrollment token
- [x] Enrollment flow: token → create account → enrolled = true
- [x] Firm dashboard: stats (appointments, callbacks, rating, recent activity)
- [x] Firm profile: view/edit contact info
- [x] Firm pricing: CRUD price cards (bands, adjustments, disbursements)
- [x] Admin endpoint: list orgs, generate enrollment token + email

### Phase 3 — Probate Chat Interface ✅
- [x] Backend: `POST /api/public/sessions` — create + return first question
- [x] Backend: `POST /api/public/sessions/{id}/answer` — next question or complete
- [x] Backend: `POST /api/public/sessions/{id}/save` — email resume URL
- [x] Backend: 13-step question flow engine with branching logic
- [x] Frontend: full chat UI (message bubbles, option chips, postcode input, progress bar, answer sidebar, save modal)

### Phase 4 — Price Calculation + Results ✅
- [x] Price calculator: bands → base fee → adjustments → VAT → disbursements → total
- [x] Search service: enrolled orgs + price cards → calculate quotes → rank (price/reputation/distance)
- [x] Results page: sortable table, enrolled (rank 1-5) vs non-enrolled, quote breakdown

### Phase 5 — Appointment & Callback ✅
- [x] Backend: `POST /api/public/appointments` (appoint|callback)
- [x] Email: consumer confirmation + firm notification via Sparkpost
- [x] Frontend: Appoint modal (name, email, consent, quote)
- [x] Frontend: Callback modal (name, email, phone, preferred time)

### Phase 6-7 — Reviews ✅
- [x] Google Places Place ID search on firm enrollment
- [x] Weekly APScheduler job: fetch Google reviews → store → recalculate aggregate
- [x] Aggregate rating: CML reviews 2x weight, Google 1x weight
- [x] Daily APScheduler job: send review invitations after ~90 days
- [x] Review form (`/review/[token]`): star rating + text
- [x] Firm dashboard: view reviews, submit response, report review

### Phase 8 — Marketing Pages ✅
- [x] Homepage with probate chat CTA
- [x] How It Works page
- [x] For Law Firms page
- [x] Probate landing page (SEO-optimised)
- [x] Contact, Privacy Policy, Terms pages
- [x] Shared Navbar + Footer components

### Phase 9 — Polish & Production Deploy (TODO)
- [ ] Rate limiting middleware (slowapi — configured in main.py, needs testing)
- [ ] Cookie consent banner
- [ ] Railway `railway.toml` / `Procfile` for deployment
- [ ] Cloudflare DNS setup
- [ ] End-to-end smoke test

---

## API Keys / Accounts Needed

| Service | Action |
|---|---|
| Google Places API | Enable in Google Cloud Console, create restricted API key |
| Sparkpost | Create account, verify sending domain (choosemylawyer.co.uk) |
| Fetchify.io | Register for UK postcode lookup API key |
| Railway | Create account, new project, add PostgreSQL plugin |
| Cloudflare | Add domain, point nameservers, configure DNS to Railway |

---

## Local Development

```bash
# 1. Copy env
cp .env.example .env
# Edit .env with your API keys

# 2. Start all services
docker-compose up

# 3. Run migrations
docker-compose exec backend alembic upgrade head

# 4. Import SRA data (optional)
docker-compose exec backend python scripts/import_sra_csv.py --csv /path/to/sra_firms.csv --region "London"

# 5. Access
#   Frontend: http://localhost:3000
#   API docs:  http://localhost:8000/api/docs
```

---

## Verification / Testing

- **Local**: `docker-compose up` → `localhost:3000` chat → complete 13-step probate flow → results appear
- **Data import**: run `python scripts/import_sra_csv.py` → check organisations + offices in DB
- **Firm enrollment**: click enrollment link → create account → add probate pricing → appears in results
- **Appointment**: consumer appoints firm → both receive correct emails
- **Google Reviews**: manually trigger sync → reviews appear against firm in results
- **Review invitation**: manually trigger review job for test appointment → form works, review appears
- **Production**: push to `main` → Railway deploys → run same flows on live domain

---

## Deferred to Phase 2 (Post-MVP)

- Conveyancing practice area
- Additional UK regions / national rollout
- AI price extraction (Jina.ai + Claude pipeline)
- Facebook + Trustpilot review aggregation
- Admin review moderation UI
- Voice input
- A/B testing
- Subscription tiers / Stripe payments
- Xero billing integration
- Welsh language support
- Embeddable firm widget
- Cookie consent banner (partially deferred)
