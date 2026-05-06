"""Integration tests for GET /api/public/search/{session_id}."""

import uuid

import pytest


async def test_search_on_incomplete_session_returns_400(client):
    create = await client.post(
        "/api/public/sessions", json={"practice_area": "residential_conveyancing"}
    )
    session_id = create.json()["session_id"]
    # Answer only one question (incomplete).
    await client.post(
        f"/api/public/sessions/{session_id}/answer",
        json={"question_id": "purchase_price", "answer": "275000"},
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
    response = await client.get(f"/api/public/search/{completed_session.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

    firm = data["results"][0]
    assert firm["name"] == enrolled_org.name
    assert firm["quote"]["total"] > 0
    # Phase D: every result row carries factor scores; one-firm sets normalise to 50.
    assert firm["factor_scores"]["reputation"] == 50.0
    assert firm["factor_scores"]["price"] == 50.0


async def test_search_top_five_extracted_from_full_market(
    client, completed_session, db_session, test_price_card
):
    """Annex One §3.5 — top-5 are drawn from the same ranking as the full
    market, never ranked separately. We seed an unenrolled firm with a
    better rating; both should appear in `results` and the unenrolled one
    should rank higher, while `top_five_contactable` only carries the
    enrolled firm.
    """
    import uuid as _uuid

    from app.models.organisation import Organisation
    from app.models.office import Office
    from app.models.price_card import PriceCard
    from tests.conftest import SAMPLE_CONVEYANCING_PRICE_CARD

    # Unenrolled WMCA firm with a stronger reputation signal.
    other = Organisation(
        sra_number="SRA888001",
        name="Aardvark Conveyancing LLP",
        enrolled=False,
        aggregate_rating=4.9,
        aggregate_review_count=400,
    )
    db_session.add(other)
    await db_session.flush()
    db_session.add(
        Office(
            org_id=other.id,
            postcode="B2 4QA",
            address_line1="2 Colmore Row",
            city="Birmingham",
            is_primary=True,
        )
    )
    db_session.add(
        PriceCard(
            org_id=other.id,
            practice_area="residential_conveyancing",
            pricing=SAMPLE_CONVEYANCING_PRICE_CARD,
            active=True,
        )
    )
    await db_session.commit()

    response = await client.get(f"/api/public/search/{completed_session.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    # Full market includes both firms.
    names = [r["name"] for r in data["results"]]
    assert "Aardvark Conveyancing LLP" in names
    # Top-5 only carries the enrolled firm.
    assert len(data["top_five_contactable"]) == 1
    assert data["top_five_contactable"][0]["enrolled"] is True


async def test_search_excludes_intervened_firm(
    client, completed_session, db_session, enrolled_org, test_price_card
):
    """§8.13 — an SRA Intervention removes the firm from results entirely."""
    enrolled_org.intervened = True
    db_session.add(enrolled_org)
    await db_session.commit()

    response = await client.get(f"/api/public/search/{completed_session.id}")
    assert response.status_code == 200
    assert response.json()["total"] == 0


async def test_search_second_call_uses_cache(
    client, completed_session, enrolled_org, test_price_card
):
    """Second search call on same session returns identical (cached) results."""
    r1 = await client.get(f"/api/public/search/{completed_session.id}")
    r2 = await client.get(f"/api/public/search/{completed_session.id}")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["results"] == r2.json()["results"]
    assert r1.json()["top_five_contactable"] == r2.json()["top_five_contactable"]
