"""Integration tests for /api/firm/auth endpoints."""

import uuid

import pytest
import pytest_asyncio


async def test_register_with_valid_token_returns_201(client, test_org):
    response = await client.post(
        "/api/firm/auth/register",
        json={
            "enrollment_token": str(test_org.enrollment_token),
            "email": "owner@testfirm.com",
            "password": "SecurePass1",
            "full_name": "Firm Owner",
            "accept_terms": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    assert data["email"] == "owner@testfirm.com"


async def test_register_with_used_token_returns_404(client, test_org):
    """Register once (which marks the token as used), then try again."""
    payload = {
        "enrollment_token": str(test_org.enrollment_token),
        "email": "first@testfirm.com",
        "password": "SecurePass1",
        "full_name": "First User",
        "accept_terms": True,
    }
    first = await client.post("/api/firm/auth/register", json=payload)
    assert first.status_code == 201

    payload["email"] = "second@testfirm.com"
    second = await client.post("/api/firm/auth/register", json=payload)
    assert second.status_code == 404


async def test_register_with_nonexistent_token_returns_404(client):
    response = await client.post(
        "/api/firm/auth/register",
        json={
            "enrollment_token": str(uuid.uuid4()),
            "email": "nobody@example.com",
            "password": "Password123",
            "full_name": "Nobody",
            "accept_terms": True,
        },
    )
    assert response.status_code == 404


async def test_register_without_accept_terms_returns_400(client, test_org):
    response = await client.post(
        "/api/firm/auth/register",
        json={
            "enrollment_token": str(test_org.enrollment_token),
            "email": "notterms@testfirm.com",
            "password": "Password123",
            "full_name": "No Terms",
            "accept_terms": False,
        },
    )
    assert response.status_code == 400


async def test_login_correct_credentials_returns_200(client, test_user):
    response = await client.post(
        "/api/firm/auth/login",
        json={"email": "admin@testfirm.com", "password": "Password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "admin@testfirm.com"


async def test_login_wrong_password_returns_401(client, test_user):
    response = await client.post(
        "/api/firm/auth/login",
        json={"email": "admin@testfirm.com", "password": "WrongPassword"},
    )
    assert response.status_code == 401


async def test_login_unknown_email_returns_401(client):
    response = await client.post(
        "/api/firm/auth/login",
        json={"email": "nobody@nowhere.com", "password": "Password123"},
    )
    assert response.status_code == 401


async def test_me_with_valid_token_returns_200(auth_client, test_user):
    response = await auth_client.get("/api/firm/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@testfirm.com"
    assert data["role"] == "admin"
    assert "user_id" in data
    assert "org_id" in data


async def test_me_without_token_returns_401(client):
    response = await client.get("/api/firm/auth/me")
    assert response.status_code == 401


# ── Admin invite-enrollment tests ────────────────────────────────────────────


@pytest_asyncio.fixture
async def org_with_email(db_session):
    """Unenrolled organisation that has an email address."""
    from app.models.organisation import Organisation

    org = Organisation(
        sra_number="SRA999010",
        name="Email Law Firm",
        email="firm@example.com",
        enrolled=False,
        enrollment_token=None,
        enrollment_token_used=False,
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


async def test_invite_enrollment_sends_token(client, org_with_email):
    response = await client.post(f"/api/admin/organisations/{org_with_email.id}/invite-enrollment")
    assert response.status_code == 200
    data = response.json()
    assert "enrollment_token" in data
    assert data["enrollment_token"]


async def test_invite_enrollment_no_email_returns_400(client, test_org):
    response = await client.post(f"/api/admin/organisations/{test_org.id}/invite-enrollment")
    assert response.status_code == 400


async def test_invite_enrollment_already_enrolled_returns_409(client, enrolled_org):
    response = await client.post(f"/api/admin/organisations/{enrolled_org.id}/invite-enrollment")
    assert response.status_code == 409


async def test_invite_enrollment_unknown_org_returns_404(client):
    response = await client.post(f"/api/admin/organisations/{uuid.uuid4()}/invite-enrollment")
    assert response.status_code == 404
