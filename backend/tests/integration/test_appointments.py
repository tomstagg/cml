"""Integration tests for POST /api/public/appointments."""

import uuid

import pytest


def _appoint_payload(org_id: str, session_id: str, appt_type: str = "appoint") -> dict:
    return {
        "session_id": session_id,
        "org_id": org_id,
        "type": appt_type,
        "client_name": "Jane Smith",
        "client_email": "jane@example.com",
        "client_phone": "07700900123",
        "preferred_time": "Monday morning",
        "quoted_price": "2073.00",
        "consent_contacted": True,
        "consent_terms": True,
    }


async def test_create_appoint_returns_201(client, completed_session, enrolled_org):
    payload = _appoint_payload(str(enrolled_org.id), str(completed_session.id), "appoint")
    response = await client.post("/api/public/appointments", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["type"] == "appoint"
    assert data["status"] == "pending"


async def test_create_callback_returns_201(client, completed_session, enrolled_org):
    payload = _appoint_payload(str(enrolled_org.id), str(completed_session.id), "callback")
    response = await client.post("/api/public/appointments", json=payload)
    assert response.status_code == 201
    assert response.json()["type"] == "callback"


async def test_missing_consent_terms_returns_422(client, completed_session, enrolled_org):
    """consent_terms is required by the schema — missing field → 422."""
    payload = _appoint_payload(str(enrolled_org.id), str(completed_session.id))
    del payload["consent_terms"]
    response = await client.post("/api/public/appointments", json=payload)
    assert response.status_code == 422


async def test_missing_consent_contacted_returns_422(client, completed_session, enrolled_org):
    """consent_contacted is required by the schema — missing field → 422."""
    payload = _appoint_payload(str(enrolled_org.id), str(completed_session.id))
    del payload["consent_contacted"]
    response = await client.post("/api/public/appointments", json=payload)
    assert response.status_code == 422


async def test_consent_false_returns_400(client, completed_session, enrolled_org):
    """Providing consent fields as False should return 400."""
    payload = _appoint_payload(str(enrolled_org.id), str(completed_session.id))
    payload["consent_terms"] = False
    response = await client.post("/api/public/appointments", json=payload)
    assert response.status_code == 400


async def test_invalid_org_id_returns_404(client, completed_session):
    payload = _appoint_payload(str(uuid.uuid4()), str(completed_session.id))
    response = await client.post("/api/public/appointments", json=payload)
    assert response.status_code == 404
