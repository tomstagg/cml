"""
Shared pytest fixtures for the CML test suite.

DB strategy:
- Each test function runs in its own event loop (pytest-asyncio default).
- A NullPool engine is used for ALL database access in tests (fixtures + app routes).
  NullPool creates a fresh connection per operation, so there is no pooled-connection
  state to leak across event loops between tests.
- app.dependency_overrides[get_db] points the FastAPI app at the same NullPool engine.
- Session-scoped sync fixture creates test_cml_db and runs alembic migrations once.
- Per-test autouse async fixture truncates all tables for isolation.
- APScheduler is patched to a no-op so it doesn't interfere with the ASGI lifespan.
- External services (email, geocoding) are graceful no-ops when API keys are absent.
"""

import asyncio
import os
import re
import subprocess
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Absolute path to backend/ — used for alembic cwd (works locally and in Docker)
BACKEND_DIR = Path(__file__).parent.parent

# ── 1. Override DATABASE_URL BEFORE any app module is imported ──────────────
_main_url = os.environ.get(
    "DATABASE_URL",
    # Fallback uses localhost — Docker always sets DATABASE_URL explicitly,
    # so this fallback only applies when running tests locally.
    "postgresql+asyncpg://cml:cml_dev_password@localhost:5432/cml_db",
)
TEST_DATABASE_URL = re.sub(r"/([^/?]+)(\?.*)?$", r"/test_cml_db\2", _main_url)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# asyncpg admin URL — used to create/drop the test database itself
_ASYNCPG_ADMIN = re.sub(
    r"postgresql\+asyncpg://",
    "postgresql://",
    re.sub(r"/([^/?]+)(\?.*)?$", r"/postgres\2", _main_url),
)

# ── 2. Import app modules (engine will use TEST_DATABASE_URL) ────────────────
from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.chat_session import ChatSession  # noqa: E402
from app.models.firm_user import FirmUser, FirmUserRole  # noqa: E402
from app.models.office import Office  # noqa: E402
from app.models.organisation import Organisation  # noqa: E402
from app.models.price_card import PriceCard  # noqa: E402
from app.services.auth import create_access_token, hash_password  # noqa: E402

# ── 3. NullPool test engine ───────────────────────────────────────────────────
# NullPool = no connection reuse; each operation gets a fresh connection in the
# current event loop.  This makes tests safe with per-function event loops.
_test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
_test_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)


async def _test_get_db():
    """Drop-in replacement for app.database.get_db using the NullPool engine."""
    async with _test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Override FastAPI's DB dependency globally for the entire test session
app.dependency_overrides[get_db] = _test_get_db

# ── Constants ────────────────────────────────────────────────────────────────
TRUNCATE_SQL = text(
    "TRUNCATE TABLE appointments, review_invitations, reviews, "
    "price_cards, firm_users, offices, chat_sessions, organisations CASCADE"
)

ALL_13_ANSWERS = {
    "service_type": "full_administration",
    "estate_value": "100k_325k",
    "has_will": "yes",
    "iht400": "no",
    "uk_domiciled": "yes",
    "uk_property_count": "1",
    "bank_account_count": "1_3",
    "investments_count": "simple",
    "overseas_assets": "no",
    "beneficiary_count": "1_2",
    "location": "SW1A 1AA",
    "location_preference": "local",
    "ranking_preference": "balanced",
}

SAMPLE_PRICE_CARD_PRICING = {
    "practice_area": "probate",
    "matter_types": ["grant_only", "full_administration"],
    "pricing_model": "band",
    "bands": [
        {"estate_value_min": 0, "estate_value_max": 325000, "fee": 1500},
        {"estate_value_min": 325000, "estate_value_max": 650000, "fee": 2500},
        {"estate_value_min": 650000, "estate_value_max": None, "fee": 3500},
    ],
    "adjustments": [{"name": "IHT400 supplement", "amount": 500, "condition": "iht400"}],
    "disbursements": [{"name": "Probate Registry fee", "amount": 273, "estimated": False}],
    "vat_applies_to_fees": True,
}


# ── Session-scoped DB setup (sync) ──────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test_cml_db and run alembic migrations once per pytest session."""

    async def _create_db():
        conn = await asyncpg.connect(_ASYNCPG_ADMIN)
        try:
            await conn.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = 'test_cml_db' AND pid <> pg_backend_pid()"
            )
            await conn.execute("DROP DATABASE IF EXISTS test_cml_db")
            await conn.execute("CREATE DATABASE test_cml_db")
        finally:
            await conn.close()

    asyncio.run(_create_db())

    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"Alembic migration failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")

    yield


# ── Per-test table truncation ────────────────────────────────────────────────
@pytest_asyncio.fixture(autouse=True)
async def clean_tables(setup_test_db):
    """Truncate all application tables after each test."""
    yield
    async with _test_engine.begin() as conn:
        await conn.execute(TRUNCATE_SQL)


# ── Unauthenticated HTTP client ──────────────────────────────────────────────
@pytest_asyncio.fixture
async def client(setup_test_db):
    """httpx AsyncClient backed by the FastAPI ASGI app (scheduler mocked out)."""
    with (
        patch("app.tasks.review_sync.start_scheduler", return_value=None),
        patch("app.tasks.review_sync.stop_scheduler", return_value=None),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac


# ── DB session for seeding ───────────────────────────────────────────────────
@pytest_asyncio.fixture
async def db_session():
    """Yield an async session for seeding test data (uses NullPool test engine)."""
    async with _test_session_factory() as session:
        yield session


# ── Organisation fixtures ────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def test_org(db_session):
    """Unenrolled organisation with a fresh enrollment token (for auth tests)."""
    org = Organisation(
        sra_number="SRA999001",
        name="Test Law Firm",
        enrollment_token=uuid.uuid4(),
        enrolled=False,
        enrollment_token_used=False,
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def enrolled_org(db_session):
    """Enrolled organisation with a primary office (for profile/pricing tests)."""
    org = Organisation(
        sra_number="SRA999002",
        name="Enrolled Law Firm",
        enrolled=True,
        enrollment_token=uuid.uuid4(),
        enrollment_token_used=True,
    )
    db_session.add(org)
    await db_session.flush()

    office = Office(
        org_id=org.id,
        postcode="SW1A 1AA",
        address_line1="1 Parliament Square",
        city="London",
        is_primary=True,
    )
    db_session.add(office)
    await db_session.commit()
    await db_session.refresh(org)
    return org


# ── User / auth fixtures ─────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def test_user(db_session, enrolled_org):
    """Admin FirmUser for enrolled_org."""
    user = FirmUser(
        org_id=enrolled_org.id,
        email="admin@testfirm.com",
        hashed_password=hash_password("Password123"),
        full_name="Test Admin",
        role=FirmUserRole.admin,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user, enrolled_org):
    """Valid JWT for test_user."""
    return create_access_token(str(test_user.id), str(enrolled_org.id))


@pytest_asyncio.fixture
async def auth_client(client, auth_token):
    """Client pre-configured with a valid Bearer token."""
    client.headers["Authorization"] = f"Bearer {auth_token}"
    yield client


# ── Price card fixture ────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def test_price_card(db_session, enrolled_org):
    """Active probate price card for enrolled_org."""
    card = PriceCard(
        org_id=enrolled_org.id,
        practice_area="probate",
        pricing=SAMPLE_PRICE_CARD_PRICING,
        active=True,
    )
    db_session.add(card)
    await db_session.commit()
    await db_session.refresh(card)
    return card


# ── Chat session fixture ──────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def completed_session(db_session):
    """ChatSession with all 13 answers completed."""
    session = ChatSession(
        id=uuid.uuid4(),
        practice_area="probate",
        answers=ALL_13_ANSWERS,
        message_history=[],
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session
