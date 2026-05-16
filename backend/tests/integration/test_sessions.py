"""Integration tests for the pathway-aware public chat session API."""

import uuid

from tests.conftest import CONVEYANCING_ANSWERS

# Question order for the canonical Buying-only journey.
BUYING_QUESTION_ORDER = [
    "transaction_type",
    "purchase_tenure_type",
    "purchase_property_value",
    "transaction_details",
    "distance_preference",
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
    assert data["current_question"]["id"] == "transaction_type"


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
        json={"question_id": "transaction_type", "answer": "buying"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pathway"] == "purchase"
    assert data["current_question"]["id"] == "purchase_tenure_type"
    assert data["answers"]["transaction_type"] == "buying"


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


async def test_unsure_tenure_keeps_question_active(client):
    """Selecting 'I'm not sure' should leave the user on the tenure step."""
    create = await client.post(
        "/api/public/sessions", json={"practice_area": "residential_conveyancing"}
    )
    session_id = create.json()["session_id"]

    await client.post(
        f"/api/public/sessions/{session_id}/answer",
        json={"question_id": "transaction_type", "answer": "buying"},
    )
    response = await client.post(
        f"/api/public/sessions/{session_id}/answer",
        json={"question_id": "purchase_tenure_type", "answer": "unsure"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_question"]["id"] == "purchase_tenure_type"
    assert data["is_complete"] is False


async def test_walk_buying_pathway_completes_flow(client):
    create = await client.post(
        "/api/public/sessions", json={"practice_area": "residential_conveyancing"}
    )
    session_id = create.json()["session_id"]

    last_response = None
    for qid in BUYING_QUESTION_ORDER:
        last_response = await client.post(
            f"/api/public/sessions/{session_id}/answer",
            json={"question_id": qid, "answer": CONVEYANCING_ANSWERS[qid]},
        )
        assert last_response.status_code == 200, (qid, last_response.json())

    data = last_response.json()
    assert data["is_complete"] is True
    assert data["current_question"] is None
    assert data["pathway"] == "purchase"


async def test_walk_combined_pathway_completes_flow(client):
    create = await client.post(
        "/api/public/sessions", json={"practice_area": "residential_conveyancing"}
    )
    session_id = create.json()["session_id"]

    answers_in_order = [
        ("transaction_type", "selling_and_buying"),
        (
            "combined_property_details",
            {
                "purchase_tenure_type": "freehold",
                "purchase_property_value": 350_000,
                "sale_tenure_type": "leasehold",
                "sale_property_value": 220_000,
            },
        ),
        ("transaction_details", ["mortgage_required", "additional_mortgage_redemption"]),
        ("distance_preference", "B1 1AA"),
    ]

    last_response = None
    for qid, value in answers_in_order:
        last_response = await client.post(
            f"/api/public/sessions/{session_id}/answer",
            json={"question_id": qid, "answer": value},
        )
        assert last_response.status_code == 200, (qid, last_response.json())

    data = last_response.json()
    assert data["is_complete"] is True
    assert data["pathway"] == "combined"


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
