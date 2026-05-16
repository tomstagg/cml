"""Integration tests for GET /api/public/search/{session_id}."""

import uuid


async def test_search_on_incomplete_session_returns_400(client):
    create = await client.post(
        "/api/public/sessions", json={"practice_area": "residential_conveyancing"}
    )
    session_id = create.json()["session_id"]
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
    assert firm["trading_name"] == enrolled_org.trading_name
    assert firm["quote"]["total"] > 0
    assert firm["factor_scores"]["reputation"] == 50.0
    assert firm["factor_scores"]["price"] == 50.0


async def test_search_top_five_extracted_from_full_market(
    client, completed_session, db_session, enrolled_org, test_price_card
):
    """Annex One §3.5 — top-5 are drawn from the same ranking as the full
    market, never ranked separately. Seed a non-pilot firm with a stronger
    reputation; both should appear in `results` but top-5 only carries the
    enrolled, active-in-pilot firm.
    """
    from app.models.office import Office
    from app.models.organisation import Organisation
    from app.models.price_card import PriceCard, PriceType
    from tests.conftest import SAMPLE_CONVEYANCING_PRICE_CARD

    other = Organisation(
        cml_firm_id="CML-T99",
        sra_number="SRA888001",
        name="Aardvark Conveyancing LLP",
        trading_name="Aardvark Conveyancing",
        enrolled=False,
        active_in_pilot=False,
        adjusted_reputation_value=5.4,
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
            price_type=PriceType.estimated,
            pricing=SAMPLE_CONVEYANCING_PRICE_CARD,
        )
    )
    await db_session.commit()

    response = await client.get(f"/api/public/search/{completed_session.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    trading_names = [r["trading_name"] for r in data["results"]]
    assert "Aardvark Conveyancing" in trading_names
    assert len(data["top_five_contactable"]) == 1
    assert data["top_five_contactable"][0]["enrolled"] is True


async def test_search_excludes_excluded_firm(
    client, completed_session, db_session, enrolled_org, test_price_card
):
    """§8.13 — an excluded firm is removed from results entirely."""
    enrolled_org.excluded = True
    db_session.add(enrolled_org)
    await db_session.commit()

    response = await client.get(f"/api/public/search/{completed_session.id}")
    assert response.status_code == 200
    assert response.json()["total"] == 0


async def test_search_second_call_uses_cache(
    client, completed_session, enrolled_org, test_price_card
):
    r1 = await client.get(f"/api/public/search/{completed_session.id}")
    r2 = await client.get(f"/api/public/search/{completed_session.id}")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["results"] == r2.json()["results"]
    assert r1.json()["top_five_contactable"] == r2.json()["top_five_contactable"]
