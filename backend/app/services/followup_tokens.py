"""HMAC-signed tokens for one-click follow-up responses.

Used by the end-of-day Callback follow-up and 5-working-day Proceed follow-up
emails. Each email contains a "yes" link and a "no" link; clicking either
hits a public capture endpoint that verifies the token and writes
``appointments.firm_contact_made``.
"""

import hashlib
import hmac
import uuid

from app.config import settings


def make_followup_token(appointment_id: uuid.UUID, answer: bool) -> str:
    """Sign (appointment_id, answer) with the app secret. Constant per (id, answer)."""
    payload = f"{appointment_id}:{'yes' if answer else 'no'}".encode()
    digest = hmac.new(settings.secret_key.encode(), payload, hashlib.sha256).hexdigest()
    return digest


def verify_followup_token(appointment_id: uuid.UUID, answer: bool, token: str) -> bool:
    return hmac.compare_digest(make_followup_token(appointment_id, answer), token)


def followup_url(appointment_id: uuid.UUID, answer: bool) -> str:
    """Public URL the consumer clicks from a follow-up email."""
    token = make_followup_token(appointment_id, answer)
    answer_str = "yes" if answer else "no"
    return f"{settings.api_url}/api/public/appointments/{appointment_id}/firm-contact?answer={answer_str}&token={token}"
