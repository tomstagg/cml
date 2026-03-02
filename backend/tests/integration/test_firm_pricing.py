"""Integration tests for /api/firm/pricing endpoints."""

import copy
import uuid

import pytest

from tests.conftest import SAMPLE_PRICE_CARD_PRICING


def _create_body() -> dict:
    return {
        "practice_area": "probate",
        "pricing": copy.deepcopy(SAMPLE_PRICE_CARD_PRICING),
    }


async def test_list_price_cards_empty_initially(auth_client):
    response = await auth_client.get("/api/firm/pricing")
    assert response.status_code == 200
    assert response.json() == []


async def test_create_price_card_returns_201(auth_client):
    response = await auth_client.post("/api/firm/pricing", json=_create_body())
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["practice_area"] == "probate"
    assert data["active"] is True


async def test_list_price_cards_contains_new_card(auth_client):
    await auth_client.post("/api/firm/pricing", json=_create_body())
    response = await auth_client.get("/api/firm/pricing")
    assert response.status_code == 200
    cards = response.json()
    assert len(cards) >= 1
    assert cards[0]["practice_area"] == "probate"


async def test_get_price_card_returns_200(auth_client):
    create = await auth_client.post("/api/firm/pricing", json=_create_body())
    card_id = create.json()["id"]

    response = await auth_client.get(f"/api/firm/pricing/{card_id}")
    assert response.status_code == 200
    assert response.json()["id"] == card_id


async def test_get_price_card_not_found_returns_404(auth_client):
    response = await auth_client.get(f"/api/firm/pricing/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_put_price_card_returns_200(auth_client):
    create = await auth_client.post("/api/firm/pricing", json=_create_body())
    card_id = create.json()["id"]

    updated_body = _create_body()
    updated_body["pricing"]["bands"][0]["fee"] = 1800

    response = await auth_client.put(f"/api/firm/pricing/{card_id}", json=updated_body)
    assert response.status_code == 200
    data = response.json()
    assert data["pricing"]["bands"][0]["fee"] == 1800


async def test_delete_price_card_deactivates_it(auth_client):
    """DELETE deactivates the card (active=False) and returns 204."""
    create = await auth_client.post("/api/firm/pricing", json=_create_body())
    card_id = create.json()["id"]

    delete_response = await auth_client.delete(f"/api/firm/pricing/{card_id}")
    assert delete_response.status_code == 204

    # Verify the card is deactivated (still retrievable, active=False)
    get_response = await auth_client.get(f"/api/firm/pricing/{card_id}")
    assert get_response.status_code == 200
    assert get_response.json()["active"] is False


async def test_preview_price_card_returns_quote(auth_client):
    create = await auth_client.post("/api/firm/pricing", json=_create_body())
    card_id = create.json()["id"]

    response = await auth_client.post(f"/api/firm/pricing/{card_id}/preview")
    assert response.status_code == 200
    data = response.json()
    assert "quote" in data
    assert data["quote"]["total"] > 0


async def test_create_price_card_unauthenticated_returns_401(client):
    response = await client.post("/api/firm/pricing", json=_create_body())
    assert response.status_code == 401


async def test_list_price_cards_unauthenticated_returns_401(client):
    response = await client.get("/api/firm/pricing")
    assert response.status_code == 401


async def test_get_price_card_unauthenticated_returns_401(client):
    response = await client.get(f"/api/firm/pricing/{uuid.uuid4()}")
    assert response.status_code == 401
