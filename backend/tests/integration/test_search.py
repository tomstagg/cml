"""Integration tests for GET /api/public/search/{session_id}."""

import uuid

import pytest

from tests.conftest import ALL_13_ANSWERS, SAMPLE_PRICE_CARD_PRICING


async def test_search_on_incomplete_session_returns_400(client):
    create = await client.post("/api/public/sessions", json={"practice_area": "probate"})
    session_id = create.json()["session_id"]
    # Answer only one question (incomplete)
    await client.post(
        f"/api/public/sessions/{session_id}/answer",
        json={"question_id": "service_type", "answer": "full_administration"},
    )

    response = await client.get(f"/api/public/search/{session_id}")
    assert response.status_code == 400


async def test_search_on_nonexistent_session_returns_404(client):
    response = await client.get(f"/api/public/search/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_search_on_complete_session_no_firms_returns_empty(client, completed_session):
    """No enrolled firms → results list is empty, not an error."""
    response = await client.get(f"/api/public/search/{completed_session.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []
    assert data["total"] == 0


async def test_search_with_enrolled_firm_returns_result(
    client, completed_session, enrolled_org, test_price_card
):
    """An enrolled firm with an active price card should appear in results."""
    response = await client.get(f"/api/public/search/{completed_session.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

    firm = data["results"][0]
    assert firm["name"] == enrolled_org.name
    assert firm["quote"]["total"] > 0
    # For the 100k_325k band + VAT: fee=1500, vat=300, disb=273 → total=2073
    assert firm["quote"]["total"] == pytest.approx(2073.0)


async def test_search_second_call_uses_cache(client, completed_session, enrolled_org, test_price_card):
    """Second search call on same session returns same results (from cache)."""
    r1 = await client.get(f"/api/public/search/{completed_session.id}")
    r2 = await client.get(f"/api/public/search/{completed_session.id}")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["results"] == r2.json()["results"]
