"""Integration tests for /api/firm/profile endpoints."""

import pytest


async def test_get_profile_returns_200(auth_client, enrolled_org):
    response = await auth_client.get("/api/firm/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == enrolled_org.name
    assert data["sra_number"] == enrolled_org.sra_number
    assert "offices" in data


async def test_get_profile_contains_offices(auth_client, enrolled_org):
    response = await auth_client.get("/api/firm/profile")
    assert response.status_code == 200
    data = response.json()
    # enrolled_org fixture creates one primary office
    assert len(data["offices"]) == 1
    assert data["offices"][0]["postcode"] == "SW1A 1AA"


async def test_patch_profile_updates_field(auth_client, enrolled_org):
    response = await auth_client.patch(
        "/api/firm/profile",
        json={"phone": "020 7000 0000"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "020 7000 0000"


async def test_patch_profile_updated_field_persists(auth_client, enrolled_org):
    """Patch then GET confirms the value was saved."""
    await auth_client.patch("/api/firm/profile", json={"phone": "01234 567890"})
    get_response = await auth_client.get("/api/firm/profile")
    assert get_response.json()["phone"] == "01234 567890"


async def test_get_profile_unauthenticated_returns_401(client):
    response = await client.get("/api/firm/profile")
    assert response.status_code == 401


async def test_patch_profile_unauthenticated_returns_401(client):
    response = await client.patch("/api/firm/profile", json={"phone": "07700 900000"})
    assert response.status_code == 401
