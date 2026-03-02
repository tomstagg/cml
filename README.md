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
