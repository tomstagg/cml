"""Email service using Sparkpost."""

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
) -> bool:
    """Send a transactional email. Returns True on success."""
    sp = _get_client()
    if sp is None:
        logger.info(f"[EMAIL MOCK] To: {to} | Subject: {subject}")
        return True

    try:
        resp = sp.transmissions.send(
            recipients=[to],
            from_email=f"{settings.sparkpost_from_name} <{settings.sparkpost_from_email}>",
            subject=subject,
            html=html,
            text=text or "",
        )
        return resp.get("total_accepted_recipients", 0) > 0
    except Exception as e:
        logger.error(f"Sparkpost error: {e}")
        return False


async def send_appointment_confirmation_consumer(
    client_email: str,
    client_name: str,
    firm_name: str,
    appointment_type: str,
    quote_total: float | None,
) -> bool:
    type_label = "appointment" if appointment_type == "appoint" else "callback request"
    subject = f"Your {type_label} with {firm_name} — Choose My Lawyer"
    html = f"""
    <h2>Your {type_label} has been submitted</h2>
    <p>Hi {client_name},</p>
    <p>Your {type_label} with <strong>{firm_name}</strong> has been submitted successfully.</p>
    {"<p>Estimated quote: <strong>£" + f"{quote_total:,.2f}" + "</strong></p>" if quote_total else ""}
    <p>The firm will be in touch with you shortly to confirm the next steps.</p>
    <p>Best regards,<br>The Choose My Lawyer Team</p>
    """
    return await send_email(client_email, subject, html)


async def send_appointment_notification_firm(
    firm_email: str,
    firm_name: str,
    client_name: str,
    client_email: str,
    client_phone: str | None,
    appointment_type: str,
    preferred_time: str | None,
    quote_total: float | None,
) -> bool:
    type_label = (
        "New appointment request" if appointment_type == "appoint" else "New callback request"
    )
    subject = f"{type_label} from Choose My Lawyer"
    html = f"""
    <h2>{type_label}</h2>
    <p>A client has requested a {appointment_type} with <strong>{firm_name}</strong> via Choose My Lawyer.</p>
    <h3>Client Details</h3>
    <ul>
        <li><strong>Name:</strong> {client_name}</li>
        <li><strong>Email:</strong> {client_email}</li>
        {"<li><strong>Phone:</strong> " + client_phone + "</li>" if client_phone else ""}
        {"<li><strong>Preferred time:</strong> " + preferred_time + "</li>" if preferred_time else ""}
        {"<li><strong>Quoted price:</strong> £" + f"{quote_total:,.2f}" + "</li>" if quote_total else ""}
    </ul>
    <p>Please contact the client as soon as possible to confirm their {appointment_type}.</p>
    """
    return await send_email(firm_email, subject, html)


async def send_enrollment_invitation(
    firm_email: str,
    firm_name: str,
    enrollment_url: str,
) -> bool:
    subject = f"Join Choose My Lawyer — Enrollment invitation for {firm_name}"
    html = f"""
    <h2>You've been invited to join Choose My Lawyer</h2>
    <p>Dear {firm_name},</p>
    <p>Choose My Lawyer is a new UK legal comparison platform helping consumers find probate solicitors.</p>
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
    subject = "Your probate quote — saved for later"
    html = f"""
    <h2>Your probate solicitor comparison</h2>
    <p>You asked us to save your progress. Click the link below to pick up where you left off:</p>
    <p><a href="{resume_url}" style="background:#0d9488;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;display:inline-block;">
        Continue Your Search
    </a></p>
    <p>This link will expire in 30 days.</p>
    <p>Best regards,<br>The Choose My Lawyer Team</p>
    """
    return await send_email(client_email, subject, html)


async def send_review_invitation(
    client_email: str,
    firm_name: str,
    review_url: str,
) -> bool:
    subject = f"How was your experience with {firm_name}?"
    html = f"""
    <h2>Share your experience</h2>
    <p>You recently used {firm_name} for probate services through Choose My Lawyer.</p>
    <p>Would you mind leaving a quick review? It only takes a minute and helps others find great solicitors.</p>
    <p><a href="{review_url}" style="background:#0d9488;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;display:inline-block;">
        Leave a Review
    </a></p>
    <p>This link will expire in 30 days.</p>
    <p>Best regards,<br>The Choose My Lawyer Team</p>
    """
    return await send_email(client_email, subject, html)
