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

BACKEND_DIR = Path(__file__).parent.parent

# ── 1. Override env vars BEFORE any app module is imported ──────────────────
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")

_main_url = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://cml:cml_dev_password@localhost:5432/cml_db",
)
TEST_DATABASE_URL = re.sub(r"/([^/?]+)(\?.*)?$", r"/test_cml_db\2", _main_url)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

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
from app.models.price_card import PriceCard, PriceType  # noqa: E402
from app.services.auth import create_access_token, hash_password  # noqa: E402

# ── 3. NullPool test engine ───────────────────────────────────────────────────
_test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
_test_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)


async def _test_get_db():
    async with _test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = _test_get_db

# ── Constants ────────────────────────────────────────────────────────────────
TRUNCATE_SQL = text(
    "TRUNCATE TABLE appointments, review_invitations, reviews, "
    "price_cards, firm_users, offices, chat_sessions, "
    "complaints_summary, regulatory_summary, organisations, "
    "analytics_events CASCADE"
)

# Canonical conveyancing intake answers for the new pathway-aware schema.
# Represents a Buying-only journey through the chat. Contact details are
# captured at Proceed/Callback, not during intake.
CONVEYANCING_ANSWERS = {
    "transaction_type": "buying",
    "purchase_tenure_type": "leasehold",
    "purchase_property_value": 275_000,
    "transaction_details": ["mortgage_required", "shared_ownership_or_help_to_buy"],
    "distance_preference": "B1 1AA",
}

ALL_ANSWERS = CONVEYANCING_ANSWERS

# Sample price card in the new Master Export verbatim shape.
SAMPLE_CONVEYANCING_PRICE_CARD = {
    "freehold": {
        "purchase": {
            150000: 950,
            250000: 1150,
            500000: 1450,
            750000: 1750,
            1000000: 2000,
            1250000: 2300,
            1500000: 2600,
        },
        "sale": {
            150000: 900,
            250000: 1100,
            500000: 1400,
            750000: 1700,
            1000000: 1950,
            1250000: 2250,
            1500000: 2550,
        },
    },
    "leasehold": {
        "purchase": {
            150000: 1050,
            250000: 1250,
            500000: 1550,
            750000: 1850,
            1000000: 2100,
            1250000: 2400,
            1500000: 2700,
        },
        "sale": {
            150000: 1000,
            250000: 1200,
            500000: 1500,
            750000: 1800,
            1000000: 2050,
            1250000: 2350,
            1500000: 2650,
        },
    },
    "modifiers": [],
    "additional_costs": [],
    "disbursements": [{"name": "Searches (CML standard pack)", "amount": 350}],
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


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(setup_test_db):
    yield
    async with _test_engine.begin() as conn:
        await conn.execute(TRUNCATE_SQL)


@pytest_asyncio.fixture
async def client(setup_test_db):
    """httpx AsyncClient backed by the FastAPI ASGI app (scheduler mocked out)."""
    with (
        patch("app.tasks.scheduler.start_scheduler", return_value=None),
        patch("app.tasks.scheduler.stop_scheduler", return_value=None),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac


@pytest_asyncio.fixture
async def db_session():
    async with _test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def verify_session():
    async with _test_session_factory() as session:
        yield session


# ── Organisation fixtures ────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def test_org(db_session):
    """Unenrolled organisation with a fresh enrollment token (for auth tests)."""
    org = Organisation(
        cml_firm_id="CML-T01",
        sra_number="SRA999001",
        name="Test Law Firm Ltd",
        trading_name="Test Law Firm",
        enrollment_token=uuid.uuid4(),
        enrolled=False,
        enrollment_token_used=False,
        conveyancing_confirmed=True,
        transparency_statement_captured=False,
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def enrolled_org(db_session):
    """Enrolled organisation with a primary office (for profile/pricing tests)."""
    org = Organisation(
        cml_firm_id="CML-T02",
        sra_number="SRA999002",
        name="Enrolled Law Firm Ltd",
        trading_name="Enrolled Law Firm",
        enrolled=True,
        enrollment_token=uuid.uuid4(),
        enrollment_token_used=True,
        conveyancing_confirmed=True,
        transparency_statement_captured=True,
        proceed_enabled=True,
        callback_enabled=True,
        active_in_pilot=True,
        referral_email="referrals@enrolledfirm.com",
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
    return create_access_token(str(test_user.id), str(enrolled_org.id))


@pytest_asyncio.fixture
async def auth_client(client, auth_token):
    client.headers["Authorization"] = f"Bearer {auth_token}"
    yield client


@pytest_asyncio.fixture
async def admin_client(client):
    client.headers["X-Admin-Key"] = "test-admin-key"
    yield client


# ── Price card fixture ────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def test_price_card(db_session, enrolled_org):
    """Verified conveyancing price card for enrolled_org."""
    card = PriceCard(
        org_id=enrolled_org.id,
        price_type=PriceType.verified,
        pricing=SAMPLE_CONVEYANCING_PRICE_CARD,
    )
    db_session.add(card)
    await db_session.commit()
    await db_session.refresh(card)
    return card


# ── Chat session fixture ──────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def completed_session(db_session):
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
