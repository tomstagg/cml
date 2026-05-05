"""Integration tests for public chat session API."""

import uuid

from tests.conftest import CONVEYANCING_ANSWERS

CONVEYANCING_QUESTION_ORDER = [
    "purchase_price",
    "tenure",
    "property_postcode",
    "mortgage",
    "new_build",
    "help_to_buy_isa",
    "shared_ownership",
    "scorecard_preference",
    "include_distance",
    "first_name",
    "last_name",
    "email",
    "phone",
]


async def test_create_session_returns_201_with_first_question(client):
    response = await client.post(
        "/api/public/sessions", json={"practice_area": "residential_conveyancing"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["is_complete"] is False
    assert data["current_question"]["step"] == 1
    assert data["current_question"]["id"] == "purchase_price"


async def test_get_session_returns_200(client):
    create = await client.post(
        "/api/public/sessions", json={"practice_area": "residential_conveyancing"}
    )
    session_id = create.json()["session_id"]

    response = await client.get(f"/api/public/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert str(data["session_id"]) == session_id


async def test_get_session_not_found_returns_404(client):
    response = await client.get(f"/api/public/sessions/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_submit_answer_advances_to_next_question(client):
    create = await client.post(
        "/api/public/sessions", json={"practice_area": "residential_conveyancing"}
    )
    session_id = create.json()["session_id"]

    response = await client.post(
        f"/api/public/sessions/{session_id}/answer",
        json={"question_id": "purchase_price", "answer": "275000"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_question"]["step"] == 2
    assert data["current_question"]["id"] == "tenure"
    assert data["answers"]["purchase_price"] == "275000"


async def test_submit_unknown_question_id_returns_400(client):
    create = await client.post(
        "/api/public/sessions", json={"practice_area": "residential_conveyancing"}
    )
    session_id = create.json()["session_id"]

    response = await client.post(
        f"/api/public/sessions/{session_id}/answer",
        json={"question_id": "nonexistent_question", "answer": "anything"},
    )
    assert response.status_code == 400


async def test_submit_invalid_postcode_returns_400(client):
    create = await client.post(
        "/api/public/sessions", json={"practice_area": "residential_conveyancing"}
    )
    session_id = create.json()["session_id"]
    # Walk to property_postcode (step 3).
    await client.post(
        f"/api/public/sessions/{session_id}/answer",
        json={"question_id": "purchase_price", "answer": "275000"},
    )
    await client.post(
        f"/api/public/sessions/{session_id}/answer",
        json={"question_id": "tenure", "answer": "leasehold"},
    )

    response = await client.post(
        f"/api/public/sessions/{session_id}/answer",
        json={"question_id": "property_postcode", "answer": "ZZ"},
    )
    assert response.status_code == 400


async def test_walk_all_answers_completes_flow_and_persists_scorecard(client):
    """All 13 conveyancing answers → is_complete=True; scorecard fields stored."""
    create = await client.post(
        "/api/public/sessions", json={"practice_area": "residential_conveyancing"}
    )
    session_id = create.json()["session_id"]

    last_response = None
    for qid in CONVEYANCING_QUESTION_ORDER:
        last_response = await client.post(
            f"/api/public/sessions/{session_id}/answer",
            json={"question_id": qid, "answer": CONVEYANCING_ANSWERS[qid]},
        )
        assert last_response.status_code == 200, (qid, last_response.json())

    data = last_response.json()
    assert data["is_complete"] is True
    assert data["current_question"] is None
    assert data["scorecard_preference"] == "balanced"
    assert data["include_distance"] is True


async def test_save_session_returns_200(client):
    create = await client.post(
        "/api/public/sessions", json={"practice_area": "residential_conveyancing"}
    )
    session_id = create.json()["session_id"]

    response = await client.post(
        f"/api/public/sessions/{session_id}/save",
        json={"email": "user@example.com"},
    )
    assert response.status_code == 200
    assert "message" in response.json()
