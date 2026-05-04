"""Integration tests for admin organisation management endpoints."""

import uuid
from unittest.mock import AsyncMock, patch


# ── Auth guard ────────────────────────────────────────────────────────────────


async def test_admin_routes_require_api_key(client):
    resp = await client.get("/api/admin/organisations")
    assert resp.status_code == 401


async def test_admin_routes_reject_wrong_key(client):
    client.headers["X-Admin-Key"] = "wrong-key"
    resp = await client.get("/api/admin/organisations")
    assert resp.status_code == 401


# ── GET /api/admin/organisations ──────────────────────────────────────────────


async def test_list_organisations_empty(admin_client):
    resp = await admin_client.get("/api/admin/organisations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["results"] == []


async def test_list_organisations_returns_all(admin_client, test_org, enrolled_org):
    resp = await admin_client.get("/api/admin/organisations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["results"]) == 2


async def test_list_organisations_filter_enrolled_true(admin_client, test_org, enrolled_org):
    resp = await admin_client.get("/api/admin/organisations?enrolled=true")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["results"][0]["enrolled"] is True


async def test_list_organisations_filter_enrolled_false(admin_client, test_org, enrolled_org):
    resp = await admin_client.get("/api/admin/organisations?enrolled=false")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["results"][0]["enrolled"] is False


async def test_list_organisations_search_by_name(admin_client, test_org, enrolled_org):
    resp = await admin_client.get("/api/admin/organisations?search=Enrolled")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert "Enrolled" in data["results"][0]["name"]


async def test_list_organisations_search_case_insensitive(admin_client, enrolled_org):
    resp = await admin_client.get("/api/admin/organisations?search=enrolled")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


async def test_list_organisations_search_no_match(admin_client, test_org):
    resp = await admin_client.get("/api/admin/organisations?search=NonexistentFirmXYZ")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["results"] == []


async def test_list_organisations_pagination_limit(admin_client, test_org, enrolled_org):
    resp = await admin_client.get("/api/admin/organisations?limit=1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["results"]) == 1


async def test_list_organisations_pagination_offset(admin_client, test_org, enrolled_org):
    resp = await admin_client.get("/api/admin/organisations?limit=1&offset=1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1


async def test_list_organisations_response_fields(admin_client, enrolled_org):
    resp = await admin_client.get("/api/admin/organisations")
    assert resp.status_code == 200
    org = resp.json()["results"][0]
    for field in ("id", "sra_number", "name", "enrolled", "auth_status"):
        assert field in org


# ── POST /api/admin/organisations/{org_id}/sync-google-place ──────────────────


async def test_sync_google_place_stores_place_id(admin_client, enrolled_org):
    with patch(
        "app.api.admin.organisations.search_google_place_id",
        new_callable=AsyncMock,
        return_value="ChIJfoundplaceid",
    ):
        resp = await admin_client.post(
            f"/api/admin/organisations/{enrolled_org.id}/sync-google-place"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["place_id"] == "ChIJfoundplaceid"
    assert "message" in data


async def test_sync_google_place_unknown_org_returns_404(admin_client):
    resp = await admin_client.post(f"/api/admin/organisations/{uuid.uuid4()}/sync-google-place")
    assert resp.status_code == 404


async def test_sync_google_place_not_found_returns_404(admin_client, enrolled_org):
    with patch(
        "app.api.admin.organisations.search_google_place_id",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await admin_client.post(
            f"/api/admin/organisations/{enrolled_org.id}/sync-google-place"
        )
    assert resp.status_code == 404
    assert "Google Place ID" in resp.json()["detail"]
