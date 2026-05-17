"""Unit tests for the email service — Sparkpost is mocked throughout."""

from unittest.mock import AsyncMock, MagicMock, patch

from app.services.email import (
    send_callback_followup,
    send_callback_to_firm,
    send_callback_user_copy,
    send_conflict_check_failed,
    send_email,
    send_enrollment_invitation,
    send_select_feedback_request,
    send_select_followup,
    send_select_to_firm,
    send_select_user_copy,
    send_session_save_email,
)


_BUYING_SUMMARY = {
    "transaction_type": "buying",
    "user_postcode": "B1 1AA",
    "buying": {"tenure": "freehold", "value": 350000, "details": ["mortgage_required"]},
    "selling": None,
}

_COMBINED_SUMMARY = {
    "transaction_type": "selling_and_buying",
    "user_postcode": "B2 4QA",
    "buying": {"tenure": "leasehold", "value": 450000, "details": ["new_lease"]},
    "selling": {"tenure": "freehold", "value": 300000, "details": []},
}


# ── send_email (core) ─────────────────────────────────────────────────────────


async def test_send_email_no_api_key_returns_true():
    with patch("app.services.email._get_client", return_value=None):
        assert await send_email("test@example.com", "Subject", "<p>Body</p>") is True


async def test_send_email_sparkpost_success():
    mock_sp = MagicMock()
    mock_sp.transmissions.send.return_value = {"total_accepted_recipients": 1}
    with patch("app.services.email._get_client", return_value=mock_sp):
        assert await send_email("test@example.com", "Subject", "<p>Body</p>") is True
    mock_sp.transmissions.send.assert_called_once()


async def test_send_email_sparkpost_exception_returns_false():
    mock_sp = MagicMock()
    mock_sp.transmissions.send.side_effect = Exception("Sparkpost down")
    with patch("app.services.email._get_client", return_value=mock_sp):
        assert await send_email("test@example.com", "Subject", "<p>Body</p>") is False


async def test_send_email_zero_accepted_returns_false():
    mock_sp = MagicMock()
    mock_sp.transmissions.send.return_value = {"total_accepted_recipients": 0}
    with patch("app.services.email._get_client", return_value=mock_sp):
        assert await send_email("test@example.com", "Subject", "<p>Body</p>") is False


async def test_send_email_passes_reply_to_and_bcc():
    """Custom from_name + reply_to + bcc must reach the SparkPost SDK."""
    mock_sp = MagicMock()
    mock_sp.transmissions.send.return_value = {"total_accepted_recipients": 1}
    with patch("app.services.email._get_client", return_value=mock_sp):
        await send_email(
            "firm@law.com",
            "Subject",
            "<p>Body</p>",
            from_name="Jane Smith",
            reply_to="jane@example.com",
            bcc=["audit@cml.co.uk"],
        )
    kwargs = mock_sp.transmissions.send.call_args.kwargs
    assert kwargs["reply_to"] == "jane@example.com"
    assert kwargs["bcc"] == ["audit@cml.co.uk"]
    assert "Jane Smith" in kwargs["from_email"]


# ── Select firm email — sent in user's name ──────────────────────────────────


async def test_select_to_firm_uses_user_name_and_reply_to():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_select_to_firm(
            "firm@law.com",
            "Bridge Street Solicitors",
            "Jane Smith",
            "jane@example.com",
            "07700900123",
            _BUYING_SUMMARY,
            "B1 1AA",
            None,
            2073.0,
            "estimated",
        )
    kwargs = mock_send.call_args.kwargs
    assert kwargs["from_name"] == "Jane Smith"
    assert kwargs["reply_to"] == "jane@example.com"
    assert kwargs["bcc"]  # CML BCC must be set


async def test_select_to_firm_includes_summary_postcode_and_price_status():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_select_to_firm(
            "firm@law.com",
            "Firm",
            "Jane",
            "j@e.com",
            "07700900000",
            _BUYING_SUMMARY,
            "B1 1AA",
            None,
            2073.0,
            "estimated",
        )
    _, _, html = mock_send.call_args.args
    assert "07700900000" in html
    assert "B1 1AA" in html
    assert "Mortgage" in html  # detail token rendered as label
    assert "2,073.00" in html
    assert "estimated" in html.lower()


async def test_select_to_firm_combined_renders_both_sides():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_select_to_firm(
            "firm@law.com",
            "Firm",
            "Jane",
            "j@e.com",
            "07700900000",
            _COMBINED_SUMMARY,
            "B1 1AA",
            "B2 4QA",
            1500.0,
            "verified",
        )
    _, _, html = mock_send.call_args.args
    assert "Buying" in html
    assert "Selling" in html
    assert "B1 1AA" in html
    assert "B2 4QA" in html
    assert "verified" in html.lower()


# ── Callback firm email ──────────────────────────────────────────────────────


async def test_callback_to_firm_includes_phone_and_availability():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_callback_to_firm(
            "firm@law.com",
            "Firm",
            "Jane",
            "j@e.com",
            "07700900000",
            "Weekdays after 5pm",
            None,
        )
    kwargs = mock_send.call_args.kwargs
    _, _, html = mock_send.call_args.args
    assert kwargs["from_name"] == "Jane"
    assert kwargs["reply_to"] == "j@e.com"
    assert "07700900000" in html
    assert "Weekdays after 5pm" in html


async def test_callback_to_firm_omits_optional_fields():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_callback_to_firm("firm@law.com", "Firm", "Jane", "j@e.com", None, None, None)
    _, _, html = mock_send.call_args.args
    assert "Phone" not in html
    assert "Availability" not in html


# ── Consumer copies ──────────────────────────────────────────────────────────


async def test_select_user_copy_includes_summary_and_price():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_select_user_copy(
            "jane@example.com",
            "Jane",
            "Bridge Street Solicitors",
            _BUYING_SUMMARY,
            "B1 1AA",
            None,
            2073.0,
            "estimated",
        )
    _, _, html = mock_send.call_args.args
    assert "Bridge Street Solicitors" in html
    assert "B1 1AA" in html
    assert "2,073.00" in html
    assert "next working day" in html.lower()


async def test_callback_user_copy_confirms_availability():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_callback_user_copy(
            "jane@example.com", "Jane", "Firm", "Weekdays after 5pm", None
        )
    _, _, html = mock_send.call_args.args
    assert "Weekdays after 5pm" in html


# ── Follow-ups ───────────────────────────────────────────────────────────────


async def test_callback_followup_includes_yes_no_links():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_callback_followup(
            "jane@example.com",
            "Jane",
            "Firm",
            "https://api/yes-link",
            "https://api/no-link",
        )
    _, _, html = mock_send.call_args.args
    assert "https://api/yes-link" in html
    assert "https://api/no-link" in html


async def test_select_followup_warns_about_price_drift():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_select_followup("jane@example.com", "Jane", "Firm", "https://yes", "https://no")
    _, _, html = mock_send.call_args.args
    assert "price" in html.lower()


async def test_select_feedback_request_links_review_url():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_select_feedback_request(
            "jane@example.com", "Firm", "https://example.com/review/abc"
        )
    _, _, html = mock_send.call_args.args
    assert "https://example.com/review/abc" in html


# ── Conflict-check failure ───────────────────────────────────────────────────


async def test_conflict_check_failed_links_back_to_results():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_conflict_check_failed(
            "jane@example.com",
            "Jane",
            "Firm",
            "https://app/results/abcd",
        )
    _, _, html = mock_send.call_args.args
    assert "https://app/results/abcd" in html
    assert "conflict" in html.lower()


# ── Existing CML emails (unchanged) ──────────────────────────────────────────


async def test_enrollment_invitation_contains_url_and_firm_name():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_enrollment_invitation(
            "firm@law.com", "Test Law Firm", "http://example.com/enroll/abc123"
        )
    _, subject, html = mock_send.call_args.args
    assert "Test Law Firm" in subject
    assert "http://example.com/enroll/abc123" in html


async def test_session_save_email_contains_resume_url():
    with patch("app.services.email.send_email", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await send_session_save_email("client@example.com", "http://example.com/resume/xyz")
    to, _, html = mock_send.call_args.args
    assert to == "client@example.com"
    assert "http://example.com/resume/xyz" in html
