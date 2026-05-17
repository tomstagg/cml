"""Integration tests for POST /api/public/appointments."""

import uuid


def _select_payload(org_id: str, session_id: str) -> dict:
    return {
        "session_id": session_id,
        "org_id": org_id,
        "type": "select",
        "client_name": "Jane Smith",
        "client_email": "jane@example.com",
        "client_phone": "07700900123",
        "quoted_price": "2073.00",
        "data_sharing_consent": True,
        "purchase_property_postcode": "B1 1AA",
        "price_type": "estimated",
    }


def _callback_payload(org_id: str, session_id: str) -> dict:
    return {
        "session_id": session_id,
        "org_id": org_id,
        "type": "callback",
        "client_name": "Jane Smith",
        "client_email": "jane@example.com",
        "client_phone": "07700900123",
        "preferred_time": "Monday morning",
        "quoted_price": "2073.00",
        "consent_contacted": True,
        "consent_terms": True,
    }


async def test_create_select_returns_201(client, completed_session, enrolled_org):
    payload = _select_payload(str(enrolled_org.id), str(completed_session.id))
    response = await client.post("/api/public/appointments", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["type"] == "select"
    assert data["status"] == "pending"


async def test_create_callback_returns_201(client, completed_session, enrolled_org):
    payload = _callback_payload(str(enrolled_org.id), str(completed_session.id))
    response = await client.post("/api/public/appointments", json=payload)
    assert response.status_code == 201
    assert response.json()["type"] == "callback"


async def test_select_missing_data_sharing_consent_returns_400(
    client, completed_session, enrolled_org
):
    """The single hard-stop on the Select form is data-sharing consent."""
    payload = _select_payload(str(enrolled_org.id), str(completed_session.id))
    payload["data_sharing_consent"] = False
    response = await client.post("/api/public/appointments", json=payload)
    assert response.status_code == 400


async def test_select_missing_phone_returns_400(client, completed_session, enrolled_org):
    """Phone is required on the Select form (the spec lists it under
    `Required` in Q1 — Contact and property details)."""
    payload = _select_payload(str(enrolled_org.id), str(completed_session.id))
    payload.pop("client_phone")
    response = await client.post("/api/public/appointments", json=payload)
    assert response.status_code == 400


async def test_callback_missing_consent_terms_returns_400(client, completed_session, enrolled_org):
    """Legacy callback flow keeps the two-checkbox consent model."""
    payload = _callback_payload(str(enrolled_org.id), str(completed_session.id))
    payload["consent_terms"] = False
    response = await client.post("/api/public/appointments", json=payload)
    assert response.status_code == 400


async def test_invalid_org_id_returns_404(client, completed_session):
    payload = _select_payload(str(uuid.uuid4()), str(completed_session.id))
    response = await client.post("/api/public/appointments", json=payload)
    assert response.status_code == 404
