# Choose My Lawyer

UK legal comparison platform for probate — England & Wales.

See `PLAN.md` for architecture decisions and phase status, and `docs/cml-technical_scoping.pdf` for the full functional spec.

---

## Local development

```bash
# Start all services (PostgreSQL+PostGIS, FastAPI, Next.js)
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
uv sync --extra dev
```


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
- `offices` row: primary office with postcode (+ PostGIS point if `--geocode`)

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

## access database

docker-compose exec db psql -U cml -d cml_db


## todo

- setup github actions for build and push to railway
- configure railway to 