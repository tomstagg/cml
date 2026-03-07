"""Integration tests for public chat session API."""

import uuid

import pytest

from tests.conftest import ALL_13_ANSWERS


async def test_create_session_returns_201_with_first_question(client):
    response = await client.post("/api/public/sessions", json={"practice_area": "probate"})
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["is_complete"] is False
    assert data["current_question"]["step"] == 1
    assert data["current_question"]["id"] == "service_type"


async def test_get_session_returns_200(client):
    create = await client.post("/api/public/sessions", json={"practice_area": "probate"})
    session_id = create.json()["session_id"]

    response = await client.get(f"/api/public/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert str(data["session_id"]) == session_id


async def test_get_session_not_found_returns_404(client):
    response = await client.get(f"/api/public/sessions/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_submit_answer_advances_to_next_question(client):
    create = await client.post("/api/public/sessions", json={"practice_area": "probate"})
    session_id = create.json()["session_id"]

    response = await client.post(
        f"/api/public/sessions/{session_id}/answer",
        json={"question_id": "service_type", "answer": "full_administration"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_question"]["step"] == 2
    assert data["current_question"]["id"] == "estate_value"
    assert data["answers"]["service_type"] == "full_administration"


async def test_submit_unknown_question_id_returns_400(client):
    create = await client.post("/api/public/sessions", json={"practice_area": "probate"})
    session_id = create.json()["session_id"]

    response = await client.post(
        f"/api/public/sessions/{session_id}/answer",
        json={"question_id": "nonexistent_question", "answer": "anything"},
    )
    assert response.status_code == 400


async def test_walk_all_13_answers_completes_flow(client):
    """Submit all 13 answers sequentially and verify is_complete=True."""
    create = await client.post("/api/public/sessions", json={"practice_area": "probate"})
    session_id = create.json()["session_id"]

    question_order = [
        "service_type",
        "estate_value",
        "has_will",
        "iht400",
        "uk_domiciled",
        "uk_property_count",
        "bank_account_count",
        "investments_count",
        "overseas_assets",
        "beneficiary_count",
        "location",
        "location_preference",
        "ranking_preference",
    ]

    last_response = None
    for qid in question_order:
        last_response = await client.post(
            f"/api/public/sessions/{session_id}/answer",
            json={"question_id": qid, "answer": ALL_13_ANSWERS[qid]},
        )
        assert last_response.status_code == 200

    data = last_response.json()
    assert data["is_complete"] is True
    assert data["current_question"] is None


async def test_save_session_returns_200(client):
    create = await client.post("/api/public/sessions", json={"practice_area": "probate"})
    session_id = create.json()["session_id"]

    response = await client.post(
        f"/api/public/sessions/{session_id}/save",
        json={"email": "user@example.com"},
    )
    assert response.status_code == 200
    assert "message" in response.json()
