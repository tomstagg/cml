"""Integration tests for POST /api/public/callbacks/bulk."""

import uuid

import pytest_asyncio

from app.models.appointment import Appointment, AppointmentType
from app.models.office import Office
from app.models.organisation import Organisation


@pytest_asyncio.fixture
async def two_enrolled_orgs(db_session, enrolled_org):
    """Second enrolled firm so we can test the multi-firm path."""
    org = Organisation(
        cml_firm_id="CML-T03",
        sra_number="SRA999003",
        name="Beta Law Firm Ltd",
        trading_name="Beta Law",
        enrolled=True,
        enrollment_token=uuid.uuid4(),
        enrollment_token_used=True,
        conveyancing_confirmed=True,
        transparency_statement_captured=True,
        proceed_enabled=True,
        callback_enabled=True,
        active_in_pilot=True,
        referral_email="referrals@betalaw.com",
    )
    db_session.add(org)
    await db_session.flush()
    db_session.add(
        Office(
            org_id=org.id,
            postcode="B1 1AA",
            address_line1="2 Broad Street",
            city="Birmingham",
            is_primary=True,
        )
    )
    await db_session.commit()
    await db_session.refresh(org)
    return [enrolled_org, org]


def _payload(session_id: str, firms: list[Organisation], **over) -> dict:
    base = {
        "session_id": session_id,
        "client_name": "Jane Smith",
        "client_email": "jane@example.com",
        "client_phone": "07700900123",
        "preferred_callback_window": "11:00-13:00",
        "data_sharing_consent": True,
        "firms": [
            {
                "org_id": str(f.id),
                "quoted_price": "1850.00",
                "price_type": "estimated",
            }
            for f in firms
        ],
    }
    base.update(over)
    return base


async def test_bulk_callback_201_creates_n_appointments(
    client, completed_session, two_enrolled_orgs, db_session
):
    payload = _payload(str(completed_session.id), two_enrolled_orgs)
    response = await client.post("/api/public/callbacks/bulk", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["created"] == 2
    assert len(body["appointment_ids"]) == 2

    from sqlalchemy import select

    rows = (
        (
            await db_session.execute(
                select(Appointment).where(Appointment.session_id == completed_session.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 2
    for r in rows:
        assert r.type == AppointmentType.callback
        assert r.preferred_callback_window == "11:00-13:00"
        assert r.data_sharing_consent is True
        assert r.preferred_time is None
        assert r.consent_contacted is False
        assert r.consent_terms is False
        assert r.client_phone == "07700900123"


async def test_bulk_callback_returns_409_when_locked(
    client, completed_session, two_enrolled_orgs, db_session
):
    db_session.add(
        Appointment(
            session_id=completed_session.id,
            org_id=two_enrolled_orgs[0].id,
            type=AppointmentType.callback.value,
            client_name="Pre-existing",
            client_email="pre@example.com",
            client_phone="07700900000",
            preferred_callback_window="09:00-11:00",
            data_sharing_consent=True,
        )
    )
    await db_session.commit()

    payload = _payload(str(completed_session.id), [two_enrolled_orgs[1]])
    response = await client.post("/api/public/callbacks/bulk", json=payload)
    assert response.status_code == 409


async def test_bulk_callback_returns_404_for_unknown_firm(client, completed_session, enrolled_org):
    payload = {
        "session_id": str(completed_session.id),
        "client_name": "Jane Smith",
        "client_email": "jane@example.com",
        "client_phone": "07700900123",
        "preferred_callback_window": "13:00-15:00",
        "data_sharing_consent": True,
        "firms": [{"org_id": str(uuid.uuid4())}],
    }
    response = await client.post("/api/public/callbacks/bulk", json=payload)
    assert response.status_code == 404


async def test_bulk_callback_returns_422_for_consent_false(client, completed_session, enrolled_org):
    payload = _payload(
        str(completed_session.id),
        [enrolled_org],
        data_sharing_consent=False,
    )
    response = await client.post("/api/public/callbacks/bulk", json=payload)
    assert response.status_code == 422


async def test_bulk_callback_returns_422_for_invalid_window(
    client, completed_session, enrolled_org
):
    payload = _payload(
        str(completed_session.id),
        [enrolled_org],
        preferred_callback_window="anytime",
    )
    response = await client.post("/api/public/callbacks/bulk", json=payload)
    assert response.status_code == 422


async def test_bulk_callback_returns_422_for_four_firms(
    client, completed_session, two_enrolled_orgs
):
    payload = _payload(str(completed_session.id), two_enrolled_orgs)
    payload["firms"].extend([{"org_id": str(uuid.uuid4())}, {"org_id": str(uuid.uuid4())}])
    response = await client.post("/api/public/callbacks/bulk", json=payload)
    assert response.status_code == 422


async def test_bulk_callback_dispatches_emails(
    client, completed_session, two_enrolled_orgs, monkeypatch
):
    calls = {"firm": [], "user": []}

    async def fake_firm(*args, **kwargs):
        calls["firm"].append((args, kwargs))
        return True

    async def fake_user(*args, **kwargs):
        calls["user"].append((args, kwargs))
        return True

    monkeypatch.setattr("app.api.public.callbacks.send_callback_to_firm", fake_firm)
    monkeypatch.setattr("app.api.public.callbacks.send_bulk_callbacks_user_copy", fake_user)

    payload = _payload(str(completed_session.id), two_enrolled_orgs)
    response = await client.post("/api/public/callbacks/bulk", json=payload)
    assert response.status_code == 201

    assert len(calls["firm"]) == 2  # one per firm (both have referral_email)
    assert len(calls["user"]) == 1


async def test_callbacks_locked_false_then_true(
    client, completed_session, enrolled_org, db_session
):
    r1 = await client.get(f"/api/public/search/{completed_session.id}")
    assert r1.status_code == 200
    assert r1.json()["callbacks_locked"] is False

    db_session.add(
        Appointment(
            session_id=completed_session.id,
            org_id=enrolled_org.id,
            type=AppointmentType.callback.value,
            client_name="Sealed",
            client_email="x@example.com",
            client_phone="07700900000",
            preferred_callback_window="09:00-11:00",
            data_sharing_consent=True,
        )
    )
    await db_session.commit()

    r2 = await client.get(f"/api/public/search/{completed_session.id}")
    assert r2.status_code == 200
    assert r2.json()["callbacks_locked"] is True
