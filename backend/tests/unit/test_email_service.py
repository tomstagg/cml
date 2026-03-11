"""Unit tests for email service — all external calls are mocked."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.email import (
    send_appointment_confirmation_consumer,
    send_appointment_notification_firm,
    send_email,
    send_enrollment_invitation,
    send_review_invitation,
    send_session_save_email,
)


# ── send_email (core) ─────────────────────────────────────────────────────────


async def test_send_email_no_api_key_returns_true():
    """No Sparkpost key → mock mode, always returns True."""
    with patch("app.services.email._get_client", return_value=None):
        result = await send_email("test@example.com", "Subject", "<p>Body</p>")
    assert result is True


async def test_send_email_sparkpost_success():
    mock_sp = MagicMock()
    mock_sp.transmissions.send.return_value = {"total_accepted_recipients": 1}
    with patch("app.services.email._get_client", return_value=mock_sp):
        result = await send_email("test@example.com", "Subject", "<p>Body</p>")
    assert result is True
    mock_sp.transmissions.send.assert_called_once()


async def test_send_email_sparkpost_exception_returns_false():
    mock_sp = MagicMock()
    mock_sp.transmissions.send.side_effect = Exception("Sparkpost down")
    with patch("app.services.email._get_client", return_value=mock_sp):
        result = await send_email("test@example.com", "Subject", "<p>Body</p>")
    assert result is False


async def test_send_email_zero_accepted_returns_false():
    mock_sp = MagicMock()
    mock_sp.transmissions.send.return_value = {"total_accepted_recipients": 0}
    with patch("app.services.email._get_client", return_value=mock_sp):
        result = await send_email("test@example.com", "Subject", "<p>Body</p>")
    assert result is False


# ── send_appointment_confirmation_consumer ────────────────────────────────────


async def test_appointment_confirmation_appoint_type():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        result = await send_appointment_confirmation_consumer(
            "client@example.com", "Jane Smith", "Test Law Firm", "appoint", 1500.0
        )
    assert result is True
    to, subject, html = mock_send.call_args[0]
    assert to == "client@example.com"
    assert "appointment" in subject.lower()
    assert "Test Law Firm" in subject
    assert "1,500.00" in html


async def test_appointment_confirmation_callback_type():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_appointment_confirmation_consumer(
            "client@example.com", "Jane Smith", "Test Law Firm", "callback", None
        )
    _, subject, _ = mock_send.call_args[0]
    assert "callback" in subject.lower()


async def test_appointment_confirmation_no_quote_omits_price():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_appointment_confirmation_consumer(
            "client@example.com", "Jane", "Firm", "appoint", None
        )
    _, _, html = mock_send.call_args[0]
    assert "Estimated quote" not in html


async def test_appointment_confirmation_with_quote_shows_price():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_appointment_confirmation_consumer(
            "client@example.com", "Jane", "Firm", "appoint", 2750.50
        )
    _, _, html = mock_send.call_args[0]
    assert "2,750.50" in html


# ── send_appointment_notification_firm ───────────────────────────────────────


async def test_firm_notification_includes_client_details():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        result = await send_appointment_notification_firm(
            "firm@law.com",
            "Law Firm",
            "Jane Smith",
            "jane@example.com",
            "07700900000",
            "appoint",
            "Monday morning",
            1500.0,
        )
    assert result is True
    _, _, html = mock_send.call_args[0]
    assert "Jane Smith" in html
    assert "jane@example.com" in html
    assert "07700900000" in html
    assert "Monday morning" in html
    assert "1,500.00" in html


async def test_firm_notification_omits_optional_fields_when_none():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_appointment_notification_firm(
            "firm@law.com",
            "Law Firm",
            "Jane Smith",
            "jane@example.com",
            None,
            "callback",
            None,
            None,
        )
    _, _, html = mock_send.call_args[0]
    assert "Phone" not in html
    assert "Preferred time" not in html
    assert "Quoted price" not in html


async def test_firm_notification_callback_subject():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_appointment_notification_firm(
            "firm@law.com",
            "Firm",
            "Client",
            "c@e.com",
            None,
            "callback",
            None,
            None,
        )
    _, subject, _ = mock_send.call_args[0]
    assert "callback" in subject.lower()


# ── send_enrollment_invitation ────────────────────────────────────────────────


async def test_enrollment_invitation_contains_url_and_firm_name():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_enrollment_invitation(
            "firm@law.com", "Test Law Firm", "http://example.com/enroll/abc123"
        )
    _, subject, html = mock_send.call_args[0]
    assert "Test Law Firm" in subject
    assert "http://example.com/enroll/abc123" in html
    assert "Test Law Firm" in html


# ── send_session_save_email ───────────────────────────────────────────────────


async def test_session_save_email_contains_resume_url():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_session_save_email("client@example.com", "http://example.com/resume/xyz")
    to, _, html = mock_send.call_args[0]
    assert to == "client@example.com"
    assert "http://example.com/resume/xyz" in html


# ── send_review_invitation ────────────────────────────────────────────────────


async def test_review_invitation_contains_firm_name_and_url():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_review_invitation(
            "client@example.com", "Test Law Firm", "http://example.com/review/token123"
        )
    to, subject, html = mock_send.call_args[0]
    assert to == "client@example.com"
    assert "Test Law Firm" in subject
    assert "Test Law Firm" in html
    assert "http://example.com/review/token123" in html
