# Choose My Lawyer (CML) — Conveyancing Pilot Architecture & Task Plan

## Context & MVP scope

CML is a UK legal comparison platform. The MVP has been pivoted from probate to **residential conveyancing** for the **West Midlands Combined Authority (WMCA)**, going live on **1 June 2026** for a ~90-day PPC-driven pilot. Full requirements: `docs/requirements.md` (Annex One contains the ranking methodology). Design assets: `docs/design/` (Figma exports + `README.md` design system reference).

The pilot's purpose is commercial validation: prove users will (a) complete the journey, (b) convert via *Proceed* / *Request a callback*, and (c) generate measurable behavioural data. It is not a feature-complete product. **Speed, clarity, measurability** override completeness.

### In scope (this pilot)
- Practice area: residential conveyancing only
- Geography: WMCA postcodes (B / CV / DY / WV / WS)
- Intake: hybrid conversational chat + Figma stepper sidebar
- Pricing: Quoted Prices only (firm-supplied via portal or seed)
- Ranking: 6-factor balanced scorecard + 6 prioritised variants, full-market ranking with top-5 contactable extracted
- LeO complaints + SRA regulatory data sourced from one-off manual seed CSVs
- Email matrix: Proceed / Callback (in the user's name) + end-of-day callback follow-up + 5-working-day Proceed follow-up + conflict-check outcome notification + 2-month feedback request
- Meta Pixel + backend `analytics_events` for funnel / drop-off / conversion tracking

### Out of scope / deferred
- Knowledge + FAQ marketing pages (Figma exists; build post-pilot)
- Estimated Price path (confidence factor `c=0.075`) and estimated-disbursement factor `d=0.02`
- Daily SRA decisions scrape + 7-day reconciliation
- AI price extraction from transparency statements
- Practice areas other than conveyancing
- Conveyancing case management / payment integration
- Welsh language / national rollout

### Inherited from probate MVP (already shipped — Phases 0–8 of prior plan)
- Monorepo + docker-compose + Railway-ready FastAPI / Next.js 15 / PostgreSQL skeleton
- Alembic + 0001 initial schema (`organisations`, `offices`, `price_cards`, `chat_sessions`, `appointments`, `reviews`, `review_invitations`, `firm_users`)
- JWT auth + firm enrollment via token
- Sparkpost + Google Places sync + Fetchify postcode lookup + APScheduler weekly review sync
- 86-test pytest suite (probate-keyed; will be retargeted)

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router) · TypeScript · Tailwind CSS · React Hook Form · Sonner |
| Backend | Python 3.12 · FastAPI · SQLAlchemy (async) · Alembic |
| Database | PostgreSQL 16 (JSONB for pricing + answers; lat/lng float for distance) |
| Background | APScheduler in-process with FastAPI |
| Email | Sparkpost |
| Reviews | Google Places API (weekly sync) |
| Postcode | Fetchify.io (UK postcode → lat/lng) |
| Analytics | Meta Pixel + backend `analytics_events` table |
| Hosting | Railway (app + Postgres) · Cloudflare (DNS / SSL / WAF) |

---

## Architecture overview

```
Browser
  │
  ├─ Next.js (SSR + CSR)
  │    ├─ Marketing: /, /how-it-works, /legal-services, /conveyancing, /for-firms
  │    ├─ Public:    /chat, /results/[sessionId], /review/[token]
  │    └─ Firm:      /firm/login, /firm/enroll/[token], /firm/dashboard,
  │                  /firm/firm-details, /firm/fees, /firm/reviews
  │
  ▼
FastAPI Backend (REST)
  ├─ /api/public/    chat sessions · search · appointments · reviews · events
  ├─ /api/firm/      authenticated firm portal
  └─ /api/admin/     enrolment · LeO/SRA seed · conflict-check · analytics export
  │
  └─ APScheduler
        ├─ Weekly: Google Reviews sync
        ├─ End-of-day: Callback follow-up emails
        ├─ Daily: 5-working-day Proceed follow-ups
        └─ Daily: 2-month Proceed feedback requests

PostgreSQL
  ├─ organisations         (SRA firms; intervened flag; enrolment state)
  ├─ offices               (lat/lng for geodesic distance)
  ├─ price_cards           (Quoted Price band schema; conveyancing JSONB)
  ├─ chat_sessions         (conveyancing answers JSONB; scorecard preference)
  ├─ appointments          (Proceed | Callback; conflict_check_outcome; firm_contact_made)
  ├─ reviews               (CML + Google)
  ├─ review_invitations    (post-Proceed feedback tokens)
  ├─ firm_users            (auth)
  ├─ complaints_decisions  (LeO; severity × remedy amount + handling penalty)
  ├─ regulatory_decisions  (SRA + SDT; deduction values per severity)
  └─ analytics_events      (funnel / Meta Pixel mirror; CSV export)
```

### Ranking pipeline (critical sequencing)

```
1. Load ALL in-scope WMCA firms (enrolled + not enrolled)
2. Filter out any firm with intervention flag (Annex One §8.13)
3. For each firm, compute six factor scores
4. Apply weights from selected scorecard (balanced or one of 6 prioritised)
5. Sort firms by total score descending (apply tie-break order on collisions)
6. Extract top-5 contactable = highest-ranked enrolled firms
7. Return (full_market_results, top_five_contactable) to the client
```

This sequence is fundamental: top-5 contactable must come **from** the full ranking, never ranked separately, to preserve the "whole-of-market, fully independent" claim.

---

## Data model

### New tables

```sql
complaints_decisions
  id, org_id FK, leo_decision_id UNIQUE,
  decision_date DATE,
  poor_service_found BOOL,                   -- only true rows score
  provider_type VARCHAR,                      -- only "Firm SRA" / "ABS Firm SRA" included
  remedy_severity ENUM(no_remedy, non_pecuniary, fee_remedy, financial_compensation),
  remedy_amount_band ENUM(zero, b1_299, b300_749, b750_999, b1k_4999, b5k_9999,
                          b10k_14999, b15k_19999, b20k_24999, b25k_29999,
                          b30k_34999, b35k_39999, b40k_44999, b45k_49999, b50k_plus),
  unreasonable_complaint_handling BOOL,
  upheld_complaint_types TEXT[],              -- displayed under stars in UI
  source_url TEXT,
  published BOOL,                             -- false rows excluded from scoring
  ingested_at TIMESTAMPTZ

regulatory_decisions
  id, org_id FK, sra_decision_id UNIQUE,
  decision_type ENUM(rebuke, fixed_penalty, banded_a, banded_b, banded_c, banded_d,
                     unbanded, conditions, intervention,
                     sdt_under_10k, sdt_10_25k, sdt_25_75k, sdt_75_200k,
                     sdt_200_500k, sdt_500k_plus),
  decision_date DATE,
  source_url TEXT,
  published BOOL,
  ingested_at TIMESTAMPTZ

analytics_events
  id BIGSERIAL,
  session_id UUID,                            -- nullable; firm-side events have no session
  event_type ENUM(page_view, intake_started, intake_completed, results_viewed,
                  proceed, callback, scorecard_chosen),
  metadata JSONB,                              -- e.g. {"page": "/conveyancing"}
  created_at TIMESTAMPTZ
```

### Mutations on existing tables

```sql
organisations ADD COLUMN intervened BOOL DEFAULT false  -- Annex One §8.13: removes firm from results

chat_sessions ADD COLUMN scorecard_preference ENUM(balanced, reputation, price,
                                                    complaints, regulatory, distance, offices)
chat_sessions ADD COLUMN include_distance BOOL DEFAULT true

appointments ADD COLUMN firm_contact_made BOOL                       -- set by follow-up reply
appointments ADD COLUMN conflict_check_outcome ENUM(pending, clear, conflict)

price_cards / chat_sessions:
  practice_area DEFAULT 'residential_conveyancing'
```

### Conveyancing chat answers (JSONB)

```json
{
  "purchase_price": 320000,
  "tenure": "leasehold",
  "property_postcode": "B17 9LJ",
  "mortgage": true,
  "new_build": false,
  "help_to_buy_isa": false,
  "shared_ownership": false,
  "scorecard_preference": "balanced",
  "include_distance": true,
  "first_name": "Jane",
  "last_name": "Carter",
  "email": "jane@example.com",
  "phone": "07700 900123"
}
```

### Conveyancing price card JSONB (Quoted-only this pilot)

```json
{
  "practice_area": "residential_conveyancing",
  "matter_types": ["purchase", "sale", "purchase_and_sale", "remortgage"],
  "pricing_model": "band",
  "bands": [
    {"purchase_price_min": 0,      "purchase_price_max": 250000, "fee": 950},
    {"purchase_price_min": 250000, "purchase_price_max": 500000, "fee": 1250},
    {"purchase_price_min": 500000, "purchase_price_max": 1000000,"fee": 1750},
    {"purchase_price_min": 1000000,"purchase_price_max": null,   "fee": 2500}
  ],
  "adjustments": [
    {"name": "Leasehold supplement",       "amount": 250, "condition": "tenure==leasehold"},
    {"name": "New build supplement",       "amount": 200, "condition": "new_build==true"},
    {"name": "Help to Buy ISA admin",      "amount": 75,  "condition": "help_to_buy_isa==true"},
    {"name": "Shared ownership supplement","amount": 250, "condition": "shared_ownership==true"},
    {"name": "Mortgage handling",          "amount": 150, "condition": "mortgage==true"}
  ],
  "included_disbursements": [
    {"name": "Local authority search",          "amount": 180, "vat_applies": true},
    {"name": "Drainage & water search",         "amount": 65,  "vat_applies": true},
    {"name": "Environmental search",            "amount": 45,  "vat_applies": true},
    {"name": "Bankruptcy search",               "amount": 6,   "vat_applies": false},
    {"name": "Land Registry priority search",   "amount": 3,   "vat_applies": false},
    {"name": "Land Registry registration fee",  "amount": 150, "vat_applies": false}
  ],
  "excluded_disbursements_note":
    "Stamp Duty Land Tax, leasehold notice fees, ground rent apportionment, and indemnity policies are excluded — see CML disbursement classification page.",
  "vat_applies_to_fees": true
}
```

**Total Effective Price** (Annex One §10):
```
P_legal,effective = P_quoted                                          # Quoted Prices only
P_effective       = P_legal,effective × (1 + VAT)
                  + Σ included_disbursements (each item's VAT pre-applied)
```

---

## Ranking algorithm — Annex One distilled

Deterministic, rules-based, no runtime AI or subjective judgment. Identical inputs **must** always produce identical outputs.

### Scorecard weights

| Factor | Balanced | Reputation | Price | Complaints | Regulatory | Distance | Offices |
|---|---|---|---|---|---|---|---|
| Reputation | 25 | **40** | 20 | 18 | 18 | 17 | 17 |
| Price | 25 | 20 | **40** | 18 | 18 | 17 | 17 |
| Complaints | 15 | 12 | 12 | **40** | 10 | 10 | 10 |
| Regulatory | 15 | 12 | 12 | 10 | **40** | 10 | 10 |
| Distance | 10 | 8 | 8 | 7 | 7 | **40** | 6 |
| Offices | 10 | 8 | 8 | 7 | 7 | 6 | **40** |
| **Total** | 100 | 100 | 100 | 100 | 100 | 100 | 100 |

If user excludes Distance (no postcode entered), rescale the active factors of the chosen scorecard proportionally so they sum to 100 (Annex One §8.2).

### Factor formulae

- **Reputation** — `Adjusted Rating = rating × (1 + 0.025 × ln(review_count + 1))`, then min-max normalise across the results set. If max == min, all firms get 50.
- **Price** — `(P_max − P_effective) / (P_max − P_min) × 100`. If max == min, all firms get 50.
- **Complaints History** — base `100`, subtract `Σ ((severity_score × remedy_amount_score) + handling_penalty)` over each scoring decision. Severity scores: no remedy 0.5, non-pecuniary 0.3, fee remedy 0.6, financial compensation 1.0. Remedy amount band scores per Annex One §6.13. Handling penalty = 4 if `unreasonable_complaint_handling`, else 0.
- **Regulatory History** — base `100`, subtract per-decision deduction (Annex One §7.3 + §7.5: rebuke −5, fixed penalty −6, banded A/B/C/D −10/−15/−40/−60, unbanded −12, conditions −25, SDT bands −10 → −60). Intervention removes the firm from the results set entirely.
- **Distance** — geodesic between user postcode and nearest recorded office; min-max normalise (closer = higher).
- **Offices** — banded by office count: 1 → 70, 2–3 → 78, 4–6 → 85, 7–10 → 90, 11–20 → 95, 21+ → 100.

### Tie-break order (Annex One §11)
1. Higher Reputation score → 2. Higher Complaints History → 3. Higher Regulatory History →
4. Higher Price score → 5. Shorter distance → 6. More offices → 7. Alphabetical firm name.

### UI severity bands (shared by Complaints and Regulatory)

| Score | Display band | Stars |
|---|---|---|
| 100 | No history | 5/5 |
| 80–99 | Very low | 4/5 |
| 60–79 | Low | 3/5 |
| 40–59 | Moderate | 2/5 |
| 20–39 | Elevated | 1/5 |
| <20 | High | 0/5 |

---

## Conveyancing intake schema

Drives both the chat conversation flow and the right-hand stepper sidebar (`docs/design/06-chat-progress.png`).

| # | Stepper section | Field | Type | Notes |
|---|---|---|---|---|
| 1 | About your case | Purchase price | numeric £ | required |
| 2 | About your case | Tenure | freehold / leasehold | required |
| 3 | About your case | Property postcode | UK postcode | required; validated against WMCA prefixes |
| 4 | About your case | Mortgage required | yes / no | required |
| 5 | About your case | New build | yes / no | required |
| 6 | About your case | Help to Buy ISA | yes / no | required |
| 7 | About your case | Shared ownership | yes / no | required |
| 8 | Ranking preference | Balanced **or** one of six prioritised factors | enum | required |
| 9 | Ranking preference | Include distance? (postcode opt-in) | yes / no | drives factor inclusion |
| 10 | Your details | First name | text | required pre-Proceed/Callback |
| 11 | Your details | Last name | text | required pre-Proceed/Callback |
| 12 | Your details | Email | email | required pre-Proceed/Callback |
| 13 | Your details | Phone | tel | required pre-Callback |

---

## Email notification matrix

| Trigger | Recipient | Template | Notes |
|---|---|---|---|
| Proceed action | Firm | `proceed_to_firm` | **From the user's name**, not CML; CML BCC |
| Proceed action | User | `proceed_user_copy` | Includes excluded-disbursements reminder |
| Callback action | Firm | `callback_to_firm` | **From the user's name**; up to 5 firms |
| Callback action | User | `callback_user_copy` | Confirms availability window |
| End-of-day after Callback | User | `callback_followup` | Binary: did the firm contact you? |
| 5 working days after Proceed | User | `proceed_followup` | Binary: did the firm contact you? Reminder about price drift |
| Conflict-check = `conflict` (admin posts) | User | `conflict_check_failed` | Direct link back to results |
| 2 months after Proceed | User | `proceed_feedback_request` | Triggers review form via `review_invitations` token |
| Firm enrolment | Firm | `enrollment_invitation` | Existing |
| Save-for-later | User | `session_saved` | Existing; copy refreshed for conveyancing |
| Weekly: Google reviews sync | — | scheduled job | Existing |

---

## Analytics events

Backend table `analytics_events` mirrors every event, each also fired through Meta Pixel.

| Event name | Where fired | Payload |
|---|---|---|
| `page_view` | All public pages (root layout) | `{ page, referrer }` |
| `intake_started` | Chat session creation | `{ session_id }` |
| `intake_completed` | Last answer submitted | `{ session_id }` |
| `scorecard_chosen` | Scorecard picker submit | `{ session_id, preference }` |
| `results_viewed` | Results page mount | `{ session_id, top_five_count, full_count }` |
| `proceed` | Proceed modal submit | `{ session_id, org_id, quoted_price }` |
| `callback` | Callback modal submit | `{ session_id, org_ids[], quoted_prices[] }` |

Admin export: `GET /api/admin/analytics/export?from=…&to=…` → CSV.

---

## Frontend design system

Source: `docs/design/README.md` and Figma exports in `docs/design/`.

### Palette

| Token | Hex | Usage |
|---|---|---|
| `brand.teal` | `#0AE5F6` | Logo accent · top-5 row tint · "Find a lawyer" gradient start · stepper checks · "New appointments" card |
| `brand.navy` | `#080C64` | Body / heading text · footer base · stat-count badges |
| `brand.mint` | `#69E4B5` | Logo accent · "New reviews" card |
| `brand.purple` | `#9747FF` | Hero gradient · "Find a lawyer" gradient end · "Appearances in results" card · footer accent |

### Gradients
- **Hero / CTA**: `linear-gradient(135deg, #9747FF 0%, #0AE5F6 100%)` — used on hero, "Find a lawyer", "Proceed" pills, CTA banners.
- **Footer**: `linear-gradient(135deg, #080C64 0%, #3E2556 100%)` with overlaid faint geometric line motif.

### Typography
- Primary: **Inter**. Weights 300 / 500 / 700.
- Type scale: option-(b) defaults from `docs/design/README.md` (H1 60/64, H2 44/52, H3 32/40, H4 24/32, body 16/24) until Figma exact values are extracted.

### Components
- **Buttons** — pill (full radius). Primary = purple→teal gradient, white text. Secondary = navy outline pill.
- **Cards** — radius 16–24px. Subtle 1px border + soft shadow `0 8px 24px rgba(8,12,100,0.08)`.
- **Inputs** — rounded 12–16px, navy label above.
- **Intake stepper** — collapsible rows; pending = grey outline, completed = solid teal with check, active = expanded with field summary (k/v pairs right-aligned).
- **Results table** — top-5 in light-teal-tinted rows (`#EAF8FB`); full table in white rows; both share columns with sortable headers (full table only).

---

## Phased task breakdown

Each phase is a roughly-PR-sized chunk. Tasks are checkable and ordered for sensible incremental delivery. After every backend task: `cd backend && uv run ruff format . && uv run pytest -v` (all green required).

### Phase A — Foundation: data model + practice-area pivot
- [x] **A1** Alembic migration `0002_conveyancing_pivot.py` — create `complaints_decisions` and `regulatory_decisions` tables with the columns above.
- [x] **A2** Alembic migration (same revision) — create `analytics_events` table.
- [x] **A3** Alembic migration (same revision) — flip `practice_area` defaults to `'residential_conveyancing'`; add `chat_sessions.scorecard_preference`, `chat_sessions.include_distance`, `appointments.firm_contact_made`, `appointments.conflict_check_outcome`, `organisations.intervened`.
- [x] **A4** Add SQLAlchemy models: `ComplaintsDecision`, `RegulatoryDecision`, `AnalyticsEvent`. Update existing models for new columns.
- [x] **A5** Update Pydantic schemas: `app/schemas/{chat,firm,search,appointment,common}.py` for the new shapes.

### Phase B — Conveyancing intake (chat + stepper)
- [x] **B1** Replace `app/services/chat.py` `PROBATE_QUESTIONS` with `CONVEYANCING_QUESTIONS` (13 steps; validation per requirements §5.1.3).
- [x] **B2** Refresh `tests/conftest.py` `ALL_13_ANSWERS` and chat-flow tests for the conveyancing schema.
- [x] **B3** New `frontend/components/chat/IntakeStepper.tsx` per `docs/design/06-chat-progress.png`. Replace `AnswerSidebar.tsx` callers.
- [x] **B4** Rename `chat/PostcodeInput.tsx` consumers; reuse for property postcode (step 3) and distance opt-in postcode (step 9).
- [x] **B5** Add scorecard preference picker UI (Balanced + 6 prioritised) before the user reaches results.

### Phase C — Pricing (Quoted Total Effective Price)
- [x] **C1** Rewrite `app/services/price_calc.py` → `calculate_total_effective_price(price_card, answers)`. Apply each adjustment's condition expression. Apply VAT to fees and per-disbursement `vat_applies` flags. No `c` or `d` factors.
- [x] **C2** Update `tests/unit/test_price_calc.py` — conveyancing fixtures (price bands, adjustment combinations, mixed-VAT disbursements).
- [x] **C3** Rewrite `frontend/components/firm/PriceCardForm.tsx` for conveyancing — bands by purchase price, condition picker (tenure / mortgage / new_build / HtB / shared_ownership), included-disbursements editor with per-row VAT toggle.

### Phase D — Ranking engine (6-factor scorecard)
- [x] **D1** New `app/services/ranking.py` — six factor scorers per Annex One §5–9.
- [x] **D2** New `app/services/scorecard.py` — weight tables for balanced + 6 prioritised; `apply()` function; tie-break ordering.
- [x] **D3** Refactor `app/services/search.py` — load all in-scope WMCA firms, run scorers, return `(full_results, top_five_contactable)`. Remove `intervened` firms upfront.
- [x] **D4** Add `tests/unit/test_scorecard.py`; refresh `tests/integration/test_search.py` covering tie-break, prioritised scorecards, distance-excluded rescaling, intervention removal, complaints / regulatory deductions.
- [x] **D5** Seed scripts `backend/scripts/import_leo_csv.py` and `import_sra_decisions_csv.py` (LeO Remedy Type → severity → Remedy Amount → score; SRA outcome → deduction value). Anchor on LeO decision ID and SRA ID.

### Phase E — Results page redesign
- [x] **E1** Rewrite `frontend/components/results/ResultsClient.tsx` per `docs/design/02-chat.png` — top-5 light-teal-tinted table + full sortable table + pagination.
- [x] **E2** New `components/results/ComplaintsCell.tsx` and `RegulatoryCell.tsx` rendering the 0–5 star bands plus a "View source" link.
- [x] **E3** Sort handlers on full-results columns (per requirements §5.3.7.2). No sort on top-5.
- [x] **E4** Update `frontend/lib/api.ts` to send `scorecard_preference` + `include_distance`; consume new response shape.

### Phase F — User actions + email matrix
- [x] **F1** Update `app/services/email.py` — Proceed / Callback firm emails are sent **in the user's name** (display name + reply-to). Add CML BCC. Update consumer copy.
- [x] **F2** New `app/tasks/followups.py` — APScheduler jobs: end-of-day callback follow-up, 5-working-day Proceed follow-up, 2-month Proceed feedback request (replaces current 90-day review job). Wire from `app/main.py`.
- [x] **F3** Admin endpoint `POST /api/admin/appointments/{id}/conflict-check` (`{ outcome: clear | conflict }`). On `conflict`, send the user the conflict-check failure email with deep link back to results.
- [x] **F4** Update `components/results/{AppointModal,CallbackModal}.tsx` consent copy — remind users of Excluded Disbursements with a link to the CML disbursement classification article (placeholder URL).

### Phase G — Firm portal redesign
- [x] **G1** Reskin `components/firm/FirmLayout.tsx` left rail to: Dashboard / Firm Details / Fees & Service Offering / Reviews / Logout.
- [x] **G2** Rewrite `app/(firm)/dashboard/page.tsx` 2×2 grid: New appointments / Video call requests / Appearances in results / New reviews. Video calls = placeholder 0 for pilot. Appearances in results reads from `analytics_events`.
- [x] **G3** Apply new palette + gradient pills across firm portal pages.

### Phase H — Marketing re-skin
- [x] **H1** Update `frontend/tailwind.config.ts` and `frontend/app/globals.css` — palette, gradient utilities, pill button radii, card radii, Inter type scale.
- [x] **H2** Reskin `Navbar.tsx` (How it works · Legal services · Knowledge · FAQs · Firm Register/Login + gradient "Find a lawyer" pill); `Footer.tsx` (navy → purple gradient). Swap PNG logo refs to `docs/logo.svg`.
- [x] **H3** Rewrite `app/(marketing)/page.tsx` per `docs/design/01-home.png`: hero with search input + quick-tag chips → Simplifying access 3-up → Types of legal help tile grid (conveyancing tile active, others greyed) → testimonials → CTA banner.
- [x] **H4** Rewrite `app/(marketing)/how-it-works/page.tsx` for conveyancing flow.
- [x] **H5** Rewrite `app/(marketing)/for-firms/page.tsx` for conveyancing solicitors.
- [x] **H6** Replace `app/(marketing)/probate/` with `app/(marketing)/conveyancing/page.tsx` (SEO landing).
- [x] **H7** Light updates to `contact`, `privacy`, `terms` to drop probate references.

### Phase I — Analytics + Meta Pixel
- [x] **I1** Add Meta Pixel `<Script>` in root layout. Env var `NEXT_PUBLIC_META_PIXEL_ID`.
- [x] **I2** Fire pixel events at every transition listed under [Analytics events](#analytics-events).
- [x] **I3** New `POST /api/public/events` (rate-limited, no auth) writing to `analytics_events`. Frontend mirrors every Meta event here.
- [x] **I4** New `GET /api/admin/analytics/export?from=&to=` returning CSV.

### Phase J — Production readiness
- [ ] **J1** Refresh SRA firm import: `scripts/import_sra_csv.py --csv … --region "WMCA" --geocode` over WMCA postcodes.
- [ ] **J2** Run `scripts/import_leo_csv.py` for those firms (latest LeO publication snapshot).
- [ ] **J3** Run `scripts/import_sra_decisions_csv.py` for those firms (latest SRA decisions snapshot).
- [x] **J4** Pre-load Quoted Prices for participating firms via `scripts/seed_price_cards.py` (admin form deferred — redundant for MVP).
- [x] **J5** Cookie consent banner gating Meta Pixel + backend `analytics_events` mirror; persists choice in localStorage.
- [ ] **J6** End-to-end smoke test (see Verification below).
- [ ] **J7** Railway deploy + env vars; Cloudflare DNS for production domain.

---

## Critical files cheatsheet

| Area | File(s) |
|---|---|
| Migrations | `backend/alembic/versions/0002_conveyancing_pivot.py` (new) |
| Models | `backend/app/models/{chat_session,price_card,appointment,organisation}.py`; new `complaints_decision.py`, `regulatory_decision.py`, `analytics_event.py` |
| Schemas | `backend/app/schemas/{chat,firm,search,appointment,common}.py` |
| Chat schema | `backend/app/services/chat.py` |
| Pricing | `backend/app/services/price_calc.py` |
| Ranking | `backend/app/services/ranking.py` (new), `scorecard.py` (new), `search.py` (refactor) |
| Email | `backend/app/services/email.py`; new `backend/app/tasks/followups.py` |
| Admin | `backend/app/api/admin/appointments.py` (conflict-check); `backend/app/api/admin/analytics.py` (new) |
| Public events | `backend/app/api/public/events.py` (new) |
| Seed scripts | `backend/scripts/import_leo_csv.py` (new), `import_sra_decisions_csv.py` (new) |
| Tests | `backend/tests/conftest.py`; `tests/unit/{test_chat_service,test_price_calc,test_scorecard (new)}.py`; `tests/integration/{test_search,test_sessions,test_firm_pricing}.py` |
| Design tokens | `frontend/tailwind.config.ts`, `frontend/app/globals.css` |
| Layout | `frontend/components/ui/{Navbar,Footer}.tsx` |
| Marketing | `frontend/app/(marketing)/{page,how-it-works,for-firms,conveyancing,contact,privacy,terms}/page.tsx` (delete `(marketing)/probate/`) |
| Chat UI | `frontend/components/chat/{ChatInterface,IntakeStepper (new),OptionChips,PropertyPostcode}.tsx`; delete `AnswerSidebar.tsx` |
| Results UI | `frontend/components/results/{ResultsClient,FirmCard,ComplaintsCell (new),RegulatoryCell (new),AppointModal,CallbackModal}.tsx` |
| Firm portal | `frontend/components/firm/{FirmLayout,PriceCardForm}.tsx`; `frontend/app/(firm)/{dashboard,pricing}/page.tsx` |
| API client | `frontend/lib/api.ts` |

Reuse without modification: `app/services/auth.py`, `app/services/geocoding.py`, `app/services/reviews.py` (Google Places sync), `app/dependencies.py`, `app/database.py`, `app/config.py`, `frontend/lib/utils.ts`, `frontend/components/ReviewForm.tsx`.

---

## Verification

After each phase, from `backend/`:
```bash
uv run ruff format .
uv run pytest -v
```

End-to-end smoke test (Phase J6):
1. `docker-compose up`; `alembic upgrade head`; run all three seed scripts.
2. Visit `http://localhost:3000`. Click "Find a lawyer" → complete the 13-step intake (leasehold + mortgage + HtB ISA + shared ownership Y).
3. Pick "Balanced", view results. Re-run with "Reputation priority" — confirm rankings differ but full set is unchanged.
4. Confirm full WMCA market renders below the top-5 enrolled. Same firm rankings whether enrolled or not.
5. Confirm Complaints + Regulatory star displays + "View source" links resolve.
6. Click Proceed on the top firm → confirm form. Inspect Sparkpost sandbox: firm receives email **from the user's name**, user receives copy.
7. Hit `POST /api/admin/appointments/{id}/conflict-check` with `{"outcome":"conflict"}` → user gets conflict-check email with link back to results.
8. Verify scheduled jobs: end-of-day callback follow-up; 5-day Proceed follow-up; 2-month feedback request.
9. Open Meta Events Manager test events tool → events fire on each page transition.
10. Hit `GET /api/admin/analytics/export?from=…&to=…` → CSV downloads.

---

## Success criteria (requirements §11)

1. End-to-end journey works without failure.
2. Results generate accurately and deterministically.
3. Users can take action (Proceed / Callback).
4. Leads captured and delivered to firms.
5. Analytics data available and usable (CSV export + Meta dashboards).
6. Marketing tracking (Meta Pixel) functioning correctly.
7. Pilot generates measurable conversion data.
