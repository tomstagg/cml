"""Email service using Sparkpost.

Phase F email matrix
--------------------
Proceed / Callback firm emails are dispatched **in the user's name** with the
client's address as ``reply_to`` and CML BCC'd, so the firm engages with the
consumer directly rather than via a relay. Consumer copies are kept on a
neutral CML from-line.

Follow-up jobs (see ``app/tasks/followups.py``) and the admin conflict-check
flow re-use the same primitives.
"""

import logging

from app.config import settings

logger = logging.getLogger(__name__)


def _get_client():
    if not settings.sparkpost_api_key:
        return None
    try:
        from sparkpost import SparkPost

        return SparkPost(settings.sparkpost_api_key)
    except ImportError:
        logger.warning("sparkpost package not installed")
        return None


async def send_email(
    to: str,
    subject: str,
    html: str,
    text: str | None = None,
    *,
    from_name: str | None = None,
    from_email: str | None = None,
    reply_to: str | None = None,
    bcc: list[str] | None = None,
) -> bool:
    """Send a transactional email. Returns True on success.

    ``from_name`` / ``from_email`` override the CML defaults so a Proceed or
    Callback email can be presented to the firm in the consumer's name.
    """
    from_display_name = from_name or settings.sparkpost_from_name
    from_address = from_email or settings.sparkpost_from_email
    sender = f"{from_display_name} <{from_address}>"

    sp = _get_client()
    if sp is None:
        bcc_note = f" (bcc: {', '.join(bcc)})" if bcc else ""
        reply_note = f" (reply-to: {reply_to})" if reply_to else ""
        logger.info(
            f"[EMAIL MOCK] From: {sender}{reply_note}{bcc_note} | To: {to} | Subject: {subject}"
        )
        return True

    try:
        send_kwargs: dict = {
            "recipients": [to],
            "from_email": sender,
            "subject": subject,
            "html": html,
            "text": text or "",
        }
        if reply_to:
            send_kwargs["reply_to"] = reply_to
        if bcc:
            send_kwargs["bcc"] = bcc
        resp = sp.transmissions.send(**send_kwargs)
        return resp.get("total_accepted_recipients", 0) > 0
    except Exception as e:
        logger.error(f"Sparkpost error: {e}")
        return False


# ── Proceed / Callback firm emails (sent IN THE USER'S NAME) ─────────────────


def _cml_bcc() -> list[str] | None:
    """CML's audit BCC — only set if a real sender domain is configured."""
    addr = settings.sparkpost_from_email
    return [addr] if addr else None


def _format_price(value: float | None) -> str | None:
    return f"£{value:,.2f}" if value is not None else None


async def send_proceed_to_firm(
    firm_email: str,
    firm_name: str,
    client_name: str,
    client_email: str,
    quoted_price: float | None,
) -> bool:
    """Proceed email — sent to the firm under the consumer's name + reply-to."""
    subject = f"Conveyancing instruction from {client_name} via Choose My Lawyer"
    price = _format_price(quoted_price)
    quote_html = (
        f"<p>The quoted price shown to {client_name} was <strong>{price}</strong>.</p>"
        if price
        else ""
    )
    html = f"""
    <h2>Hello {firm_name},</h2>
    <p>I'd like to instruct you for my residential conveyancing matter.
    I found you through Choose My Lawyer and am ready to proceed.</p>
    {quote_html}
    <p>Please reply to this email to confirm next steps and any conflict-check
    requirements. My contact details are below.</p>
    <p>Many thanks,<br>{client_name}<br>{client_email}</p>
    <hr>
    <p style="color:#666;font-size:12px;">
        This message was generated on behalf of {client_name} via Choose My
        Lawyer. Replies go directly to {client_email}.
    </p>
    """
    return await send_email(
        firm_email,
        subject,
        html,
        from_name=client_name,
        reply_to=client_email,
        bcc=_cml_bcc(),
    )


async def send_callback_to_firm(
    firm_email: str,
    firm_name: str,
    client_name: str,
    client_email: str,
    client_phone: str | None,
    preferred_time: str | None,
    quoted_price: float | None,
) -> bool:
    """Callback request — sent to the firm under the consumer's name + reply-to."""
    subject = f"Callback request from {client_name} via Choose My Lawyer"
    price = _format_price(quoted_price)
    rows = [f"<li><strong>Email:</strong> {client_email}</li>"]
    if client_phone:
        rows.append(f"<li><strong>Phone:</strong> {client_phone}</li>")
    if preferred_time:
        rows.append(f"<li><strong>Availability:</strong> {preferred_time}</li>")
    if price:
        rows.append(f"<li><strong>Quoted price:</strong> {price}</li>")
    html = f"""
    <h2>Hello {firm_name},</h2>
    <p>Please could you call me about a residential conveyancing matter? I
    found you through Choose My Lawyer and would like to discuss before I
    instruct.</p>
    <ul>{"".join(rows)}</ul>
    <p>You can reply to this email to confirm a time.</p>
    <p>Many thanks,<br>{client_name}</p>
    <hr>
    <p style="color:#666;font-size:12px;">
        This message was generated on behalf of {client_name} via Choose My
        Lawyer. Replies go directly to {client_email}.
    </p>
    """
    return await send_email(
        firm_email,
        subject,
        html,
        from_name=client_name,
        reply_to=client_email,
        bcc=_cml_bcc(),
    )


# ── Proceed / Callback consumer copies ───────────────────────────────────────


async def send_proceed_user_copy(
    client_email: str,
    client_name: str,
    firm_name: str,
    quoted_price: float | None,
    excluded_disbursements_url: str,
) -> bool:
    subject = f"Your instruction to {firm_name} — Choose My Lawyer"
    price = _format_price(quoted_price)
    quote_html = (
        f'<div style="background:#EAF8FB;padding:12px;border-radius:8px;'
        f'text-align:center;margin:12px 0;">'
        f'<p style="margin:0;color:#080C64;">Quoted price</p>'
        f'<p style="margin:0;font-size:20px;font-weight:700;">{price}</p></div>'
        if price
        else ""
    )
    html = f"""
    <h2>Your instruction has been sent</h2>
    <p>Hi {client_name},</p>
    <p>We've passed your instruction on to <strong>{firm_name}</strong> in
    your name. They'll reply to you directly to confirm next steps and any
    conflict-check requirements.</p>
    {quote_html}
    <p><strong>Reminder about disbursements.</strong> The quoted price covers
    the firm's legal fees and the included third-party costs disclosed on
    their price card. Some matter-specific costs (e.g. Stamp Duty, leasehold
    notice fees, indemnity policies) are <em>excluded</em> and will be
    confirmed by the firm once your matter is open.
    <a href="{excluded_disbursements_url}">Read more about excluded
    disbursements</a>.</p>
    <p>If you don't hear back within a few working days, please let us know.</p>
    <p>Best regards,<br>The Choose My Lawyer Team</p>
    """
    return await send_email(client_email, subject, html)


async def send_callback_user_copy(
    client_email: str,
    client_name: str,
    firm_name: str,
    preferred_time: str | None,
    quoted_price: float | None,
) -> bool:
    subject = f"Your callback request to {firm_name} — Choose My Lawyer"
    price = _format_price(quoted_price)
    quote_html = f"<p>Quoted price: <strong>{price}</strong></p>" if price else ""
    availability_html = (
        f"<p>Availability passed to the firm: <strong>{preferred_time}</strong>.</p>"
        if preferred_time
        else ""
    )
    html = f"""
    <h2>Your callback request is on its way</h2>
    <p>Hi {client_name},</p>
    <p>We've asked <strong>{firm_name}</strong> to call you back about your
    residential conveyancing matter. They'll reply to you directly.</p>
    {availability_html}
    {quote_html}
    <p>We'll check in with you at the end of the working day to make sure the
    firm got in touch.</p>
    <p>Best regards,<br>The Choose My Lawyer Team</p>
    """
    return await send_email(client_email, subject, html)


# ── Follow-ups (driven by APScheduler) ───────────────────────────────────────


async def send_callback_followup(
    client_email: str,
    client_name: str,
    firm_name: str,
    yes_url: str,
    no_url: str,
) -> bool:
    subject = f"Did {firm_name} call you back?"
    html = f"""
    <h2>Quick check-in</h2>
    <p>Hi {client_name},</p>
    <p>Earlier today you asked <strong>{firm_name}</strong> to call you about
    your conveyancing matter. Did they get in touch?</p>
    <p>
        <a href="{yes_url}" style="background:#69E4B5;color:#080C64;padding:10px 18px;text-decoration:none;border-radius:9999px;display:inline-block;margin-right:8px;">Yes, they called</a>
        <a href="{no_url}" style="background:#fff;color:#080C64;border:1px solid #080C64;padding:10px 18px;text-decoration:none;border-radius:9999px;display:inline-block;">No, not yet</a>
    </p>
    <p>This helps us keep firms accountable. Thanks!</p>
    <p>Best regards,<br>The Choose My Lawyer Team</p>
    """
    return await send_email(client_email, subject, html)


async def send_proceed_followup(
    client_email: str,
    client_name: str,
    firm_name: str,
    yes_url: str,
    no_url: str,
) -> bool:
    subject = f"How is your matter with {firm_name} progressing?"
    html = f"""
    <h2>A quick update</h2>
    <p>Hi {client_name},</p>
    <p>It's been five working days since you instructed
    <strong>{firm_name}</strong>. Did they get in touch and confirm your
    matter?</p>
    <p>
        <a href="{yes_url}" style="background:#69E4B5;color:#080C64;padding:10px 18px;text-decoration:none;border-radius:9999px;display:inline-block;margin-right:8px;">Yes, in progress</a>
        <a href="{no_url}" style="background:#fff;color:#080C64;border:1px solid #080C64;padding:10px 18px;text-decoration:none;border-radius:9999px;display:inline-block;">No, not yet</a>
    </p>
    <p><strong>Note on price.</strong> Quoted prices on Choose My Lawyer are a
    snapshot at the time you searched. If significant time has passed before
    instructing, the firm may have updated their fees — please confirm the
    current price with them in writing before proceeding.</p>
    <p>Best regards,<br>The Choose My Lawyer Team</p>
    """
    return await send_email(client_email, subject, html)


async def send_proceed_feedback_request(
    client_email: str,
    firm_name: str,
    review_url: str,
) -> bool:
    """Sent ~2 months after Proceed; replaces the old 90-day review job."""
    subject = f"How was your experience with {firm_name}?"
    html = f"""
    <h2>Share your experience</h2>
    <p>You instructed {firm_name} via Choose My Lawyer a couple of months ago.
    Now your matter has had time to progress, would you mind leaving a quick
    review? It only takes a minute and helps other home-buyers choose well.</p>
    <p><a href="{review_url}" style="background:linear-gradient(135deg,#9747FF 0%,#0AE5F6 100%);color:white;padding:12px 24px;text-decoration:none;border-radius:9999px;display:inline-block;">
        Leave a review
    </a></p>
    <p>This link will expire in 30 days.</p>
    <p>Best regards,<br>The Choose My Lawyer Team</p>
    """
    return await send_email(client_email, subject, html)


# ── Conflict-check failure (admin posts) ─────────────────────────────────────


async def send_conflict_check_failed(
    client_email: str,
    client_name: str,
    firm_name: str,
    results_url: str,
) -> bool:
    subject = f"{firm_name} can't take on your matter — pick another solicitor"
    html = f"""
    <h2>Your chosen firm has a conflict of interest</h2>
    <p>Hi {client_name},</p>
    <p><strong>{firm_name}</strong> has let us know they can't act for you on
    this matter due to a conflict of interest. This isn't unusual and doesn't
    reflect on you — it just means they have an existing relationship with
    another party connected to the transaction.</p>
    <p>Your full ranked list of WMCA conveyancers is still available — pick a
    different firm and we'll forward your instruction in the same way.</p>
    <p><a href="{results_url}" style="background:linear-gradient(135deg,#9747FF 0%,#0AE5F6 100%);color:white;padding:12px 24px;text-decoration:none;border-radius:9999px;display:inline-block;">
        Back to your results
    </a></p>
    <p>Best regards,<br>The Choose My Lawyer Team</p>
    """
    return await send_email(client_email, subject, html)


# ── Existing CML emails (unchanged) ──────────────────────────────────────────


async def send_enrollment_invitation(
    firm_email: str,
    firm_name: str,
    enrollment_url: str,
) -> bool:
    subject = f"Join Choose My Lawyer — Enrollment invitation for {firm_name}"
    html = f"""
    <h2>You've been invited to join Choose My Lawyer</h2>
    <p>Dear {firm_name},</p>
    <p>Choose My Lawyer is a new UK legal comparison platform helping consumers find conveyancing solicitors.</p>
    <p>We'd like to invite you to create a free profile on our platform.</p>
    <p><a href="{enrollment_url}" style="background:#0d9488;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;display:inline-block;">
        Create Your Profile
    </a></p>
    <p>This invitation link expires in 30 days.</p>
    <p>Best regards,<br>The Choose My Lawyer Team</p>
    """
    return await send_email(firm_email, subject, html)


async def send_session_save_email(
    client_email: str,
    resume_url: str,
) -> bool:
    subject = "Your conveyancing quote — saved for later"
    html = f"""
    <h2>Your conveyancing solicitor comparison</h2>
    <p>You asked us to save your progress. Click the link below to pick up where you left off:</p>
    <p><a href="{resume_url}" style="background:#0d9488;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;display:inline-block;">
        Continue Your Search
    </a></p>
    <p>This link will expire in 30 days.</p>
    <p>Best regards,<br>The Choose My Lawyer Team</p>
    """
    return await send_email(client_email, subject, html)
