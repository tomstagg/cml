"""Integration tests for /api/firm/pricing endpoints (single-card model)."""

import copy

from tests.conftest import SAMPLE_CONVEYANCING_PRICE_CARD


def _body() -> dict:
    return copy.deepcopy(SAMPLE_CONVEYANCING_PRICE_CARD)


async def test_get_price_card_when_none_returns_null(auth_client):
    response = await auth_client.get("/api/firm/pricing")
    assert response.status_code == 200
    assert response.json() is None


async def test_put_price_card_creates_when_absent(auth_client):
    response = await auth_client.put("/api/firm/pricing", json=_body())
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["price_type"] == "verified"


async def test_get_returns_card_after_put(auth_client):
    await auth_client.put("/api/firm/pricing", json=_body())
    response = await auth_client.get("/api/firm/pricing")
    assert response.status_code == 200
    data = response.json()
    assert data["price_type"] == "verified"


async def test_put_price_card_updates_existing(auth_client):
    await auth_client.put("/api/firm/pricing", json=_body())
    updated = _body()
    updated["freehold"]["purchase"][150000] = 1234
    response = await auth_client.put("/api/firm/pricing", json=updated)
    assert response.status_code == 200
    data = response.json()
    # JSONB int keys round-trip to strings on the wire.
    assert data["pricing"]["freehold"]["purchase"]["150000"] == 1234


async def test_preview_price_card_returns_quote(auth_client):
    await auth_client.put("/api/firm/pricing", json=_body())
    response = await auth_client.post("/api/firm/pricing/preview")
    assert response.status_code == 200
    data = response.json()
    assert "quote" in data
    assert data["quote"]["total"] > 0


async def test_preview_when_no_card_returns_null_quote(auth_client):
    response = await auth_client.post("/api/firm/pricing/preview")
    assert response.status_code == 200
    assert response.json()["quote"] is None


async def test_put_price_card_unauthenticated_returns_401(client):
    response = await client.put("/api/firm/pricing", json=_body())
    assert response.status_code == 401


async def test_get_price_card_unauthenticated_returns_401(client):
    response = await client.get("/api/firm/pricing")
    assert response.status_code == 401
