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

# ── 1. Override env vars BEFORE any app module is imported ──────────────────
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")

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
    "price_cards, firm_users, offices, chat_sessions, organisations, "
    "complaints_decisions, regulatory_decisions, analytics_events CASCADE"
)

# Canonical conveyancing intake answers — the value for each step is exactly
# what the chat API would receive over the wire (strings). Contact details
# (name/email/phone) are captured at Proceed/Callback, not during intake.
CONVEYANCING_ANSWERS = {
    "purchase_price": "275000",
    "tenure": "leasehold",
    "property_postcode": "B1 1AA",
    "mortgage": "yes",
    "new_build": "no",
    "help_to_buy_isa": "yes",
    "shared_ownership": "no",
    "scorecard_preference": "balanced",
    "include_distance": "yes",
}

ALL_ANSWERS = CONVEYANCING_ANSWERS

SAMPLE_CONVEYANCING_PRICE_CARD = {
    "practice_area": "residential_conveyancing",
    "matter_types": ["purchase", "sale", "purchase_and_sale", "remortgage"],
    "pricing_model": "band",
    "bands": [
        {"purchase_price_min": 0, "purchase_price_max": 250_000, "fee": 950},
        {"purchase_price_min": 250_000, "purchase_price_max": 500_000, "fee": 1_250},
        {"purchase_price_min": 500_000, "purchase_price_max": None, "fee": 1_750},
    ],
    "adjustments": [
        {"name": "Leasehold supplement", "amount": 250, "condition": "tenure==leasehold"},
        {"name": "New build supplement", "amount": 200, "condition": "new_build==true"},
        {"name": "Help to Buy ISA admin", "amount": 75, "condition": "help_to_buy_isa==true"},
        {
            "name": "Shared ownership supplement",
            "amount": 250,
            "condition": "shared_ownership==true",
        },
        {"name": "Mortgage handling", "amount": 150, "condition": "mortgage==true"},
    ],
    "included_disbursements": [
        {"name": "Local authority search", "amount": 180, "vat_applies": True},
        {"name": "Drainage & water search", "amount": 65, "vat_applies": True},
        {"name": "Bankruptcy search", "amount": 6, "vat_applies": False},
        {"name": "Land Registry registration fee", "amount": 150, "vat_applies": False},
    ],
    "excluded_disbursements_note": (
        "Stamp Duty Land Tax, leasehold notice fees, ground rent apportionment, "
        "indemnity policies — see CML disbursement classification page."
    ),
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


@pytest_asyncio.fixture
async def verify_session():
    """Fresh session for asserting on writes a FastAPI request just committed.

    Distinct from ``db_session`` — that one is used to seed before the request
    runs; this one opens after, so it sees committed state without sharing
    identity-map state with the request's session.
    """
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


@pytest_asyncio.fixture
async def admin_client(client):
    """Client pre-configured with the admin API key header."""
    client.headers["X-Admin-Key"] = "test-admin-key"
    yield client


# ── Price card fixture ────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def test_price_card(db_session, enrolled_org):
    """Active conveyancing price card for enrolled_org."""
    card = PriceCard(
        org_id=enrolled_org.id,
        practice_area="residential_conveyancing",
        pricing=SAMPLE_CONVEYANCING_PRICE_CARD,
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
        practice_area="residential_conveyancing",
        answers=ALL_ANSWERS,
        message_history=[],
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session
