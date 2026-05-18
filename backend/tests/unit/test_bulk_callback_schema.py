import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.appointment import BulkCallbackCreate, BulkCallbackFirm


def _payload(**over):
    base = dict(
        session_id=uuid.uuid4(),
        client_name="Jane",
        client_email="jane@example.com",
        client_phone="07700900123",
        preferred_callback_window="11:00-13:00",
        data_sharing_consent=True,
        firms=[
            BulkCallbackFirm(
                org_id=uuid.uuid4(),
                quoted_price=Decimal("1850"),
                price_type="estimated",
            )
        ],
    )
    base.update(over)
    return base


def test_accepts_one_firm():
    BulkCallbackCreate(**_payload())


def test_accepts_three_firms():
    BulkCallbackCreate(**_payload(firms=[BulkCallbackFirm(org_id=uuid.uuid4()) for _ in range(3)]))


def test_rejects_four_firms():
    with pytest.raises(ValidationError):
        BulkCallbackCreate(
            **_payload(firms=[BulkCallbackFirm(org_id=uuid.uuid4()) for _ in range(4)])
        )


def test_rejects_zero_firms():
    with pytest.raises(ValidationError):
        BulkCallbackCreate(**_payload(firms=[]))


def test_rejects_duplicate_orgs():
    dup = uuid.uuid4()
    with pytest.raises(ValidationError):
        BulkCallbackCreate(
            **_payload(firms=[BulkCallbackFirm(org_id=dup), BulkCallbackFirm(org_id=dup)])
        )


def test_rejects_invalid_window():
    with pytest.raises(ValidationError):
        BulkCallbackCreate(**_payload(preferred_callback_window="anytime"))


def test_rejects_consent_false():
    with pytest.raises(ValidationError):
        BulkCallbackCreate(**_payload(data_sharing_consent=False))


def test_rejects_short_name():
    with pytest.raises(ValidationError):
        BulkCallbackCreate(**_payload(client_name="J"))


def test_rejects_invalid_email():
    with pytest.raises(ValidationError):
        BulkCallbackCreate(**_payload(client_email="not-an-email"))
