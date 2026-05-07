"""Unit tests for HMAC follow-up tokens."""

import uuid

from app.services.followup_tokens import (
    followup_url,
    make_followup_token,
    verify_followup_token,
)


def test_token_round_trip():
    appt = uuid.uuid4()
    yes_token = make_followup_token(appt, True)
    no_token = make_followup_token(appt, False)
    assert verify_followup_token(appt, True, yes_token)
    assert verify_followup_token(appt, False, no_token)


def test_yes_and_no_tokens_differ():
    appt = uuid.uuid4()
    assert make_followup_token(appt, True) != make_followup_token(appt, False)


def test_wrong_answer_fails_verification():
    appt = uuid.uuid4()
    yes_token = make_followup_token(appt, True)
    assert not verify_followup_token(appt, False, yes_token)


def test_wrong_appointment_fails_verification():
    appt_a = uuid.uuid4()
    appt_b = uuid.uuid4()
    token = make_followup_token(appt_a, True)
    assert not verify_followup_token(appt_b, True, token)


def test_followup_url_carries_token_and_answer():
    appt = uuid.uuid4()
    url = followup_url(appt, True)
    assert str(appt) in url
    assert "answer=yes" in url
    assert "token=" in url
