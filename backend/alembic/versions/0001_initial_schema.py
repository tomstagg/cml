"""Initial schema — conveyancing pilot (residential conveyancing, WMCA)

Revision ID: 0001
Revises:
Create Date: 2026-05-04

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── organisations ────────────────────────────────────────────────────────
    op.create_table(
        "organisations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sra_number", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("auth_status", sa.String(50), nullable=False, server_default="authorised"),
        sa.Column("website_url", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("enrolled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("enrollment_token", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("enrollment_token_used", sa.Boolean(), nullable=False, server_default="false"),
        # SRA Intervention removes a firm from results entirely (Annex One §8.13).
        sa.Column("intervened", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("google_place_id", sa.String(255), nullable=True),
        sa.Column("google_rating", sa.Float(), nullable=True),
        sa.Column("google_review_count", sa.Integer(), nullable=True),
        sa.Column("aggregate_rating", sa.Float(), nullable=True),
        sa.Column("aggregate_review_count", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sra_number"),
        sa.UniqueConstraint("enrollment_token"),
    )
    op.create_index("ix_organisations_sra_number", "organisations", ["sra_number"])
    op.create_index("ix_organisations_enrolled", "organisations", ["enrolled"])
    op.create_index("ix_organisations_intervened", "organisations", ["intervened"])

    # ── offices ──────────────────────────────────────────────────────────────
    op.create_table(
        "offices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("address_line1", sa.String(255), nullable=True),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("county", sa.String(100), nullable=True),
        sa.Column("postcode", sa.String(10), nullable=False),
        sa.Column("country", sa.String(50), nullable=False, server_default="England and Wales"),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_offices_org_id", "offices", ["org_id"])
    op.create_index("ix_offices_postcode", "offices", ["postcode"])

    # ── price_cards ──────────────────────────────────────────────────────────
    op.create_table(
        "price_cards",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "practice_area",
            sa.String(50),
            nullable=False,
            server_default="residential_conveyancing",
        ),
        sa.Column(
            "pricing", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_price_cards_org_id", "price_cards", ["org_id"])
    op.create_index("ix_price_cards_practice_area", "price_cards", ["practice_area"])
    op.create_index("ix_price_cards_active", "price_cards", ["active"])

    # ── chat_sessions ────────────────────────────────────────────────────────
    # Scorecard preference enum: balanced (default) + 6 prioritised variants.
    op.execute(
        "CREATE TYPE scorecard_preference AS ENUM ("
        "'balanced','reputation','price','complaints','regulatory','distance','offices')"
    )

    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "practice_area",
            sa.String(50),
            nullable=False,
            server_default="residential_conveyancing",
        ),
        sa.Column(
            "answers", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column(
            "message_history",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("results_cache", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "scorecard_preference",
            postgresql.ENUM(
                "balanced",
                "reputation",
                "price",
                "complaints",
                "regulatory",
                "distance",
                "offices",
                name="scorecard_preference",
                create_type=False,
            ),
            nullable=False,
            server_default="balanced",
        ),
        sa.Column("include_distance", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("save_email", sa.String(255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_sessions_expires_at", "chat_sessions", ["expires_at"])

    # ── appointments ─────────────────────────────────────────────────────────
    op.execute("CREATE TYPE appointment_type AS ENUM ('appoint', 'callback')")
    op.execute(
        "CREATE TYPE appointment_status AS ENUM ('pending', 'confirmed', 'completed', 'cancelled')"
    )
    op.execute("CREATE TYPE conflict_check_outcome AS ENUM ('pending', 'clear', 'conflict')")

    op.create_table(
        "appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM("appoint", "callback", name="appointment_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "confirmed",
                "completed",
                "cancelled",
                name="appointment_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("client_name", sa.String(255), nullable=False),
        sa.Column("client_email", sa.String(255), nullable=False),
        sa.Column("client_phone", sa.String(30), nullable=True),
        sa.Column("preferred_time", sa.String(255), nullable=True),
        sa.Column("quoted_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("quote_breakdown", sa.Text(), nullable=True),
        sa.Column("consent_contacted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("consent_terms", sa.Boolean(), nullable=False, server_default="false"),
        # End-of-day callback follow-up answer (binary: did the firm contact you?)
        sa.Column("firm_contact_made", sa.Boolean(), nullable=True),
        # Firm-side conflict-check result; default pending until an admin marks it.
        sa.Column(
            "conflict_check_outcome",
            postgresql.ENUM(
                "pending",
                "clear",
                "conflict",
                name="conflict_check_outcome",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_appointments_org_id", "appointments", ["org_id"])
    op.create_index("ix_appointments_session_id", "appointments", ["session_id"])
    op.create_index("ix_appointments_status", "appointments", ["status"])

    # ── reviews ──────────────────────────────────────────────────────────────
    op.execute("CREATE TYPE review_source AS ENUM ('cml', 'google')")

    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "source",
            postgresql.ENUM("cml", "google", name="review_source", create_type=False),
            nullable=False,
        ),
        sa.Column("rating", sa.Numeric(2, 1), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("reviewer_name", sa.String(255), nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("firm_response", sa.Text(), nullable=True),
        sa.Column("firm_response_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reported", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reviews_org_id", "reviews", ["org_id"])
    op.create_index("ix_reviews_source", "reviews", ["source"])

    # ── review_invitations ───────────────────────────────────────────────────
    op.create_table(
        "review_invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("appointment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("token", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )

    # ── firm_users ───────────────────────────────────────────────────────────
    op.execute("CREATE TYPE firm_user_role AS ENUM ('admin', 'staff')")

    op.create_table(
        "firm_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("admin", "staff", name="firm_user_role", create_type=False),
            nullable=False,
            server_default="admin",
        ),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_firm_users_email", "firm_users", ["email"])
    op.create_index("ix_firm_users_org_id", "firm_users", ["org_id"])

    # ── complaints_decisions (Legal Ombudsman) ──────────────────────────────
    # Severity band 1-5 + Remedy Amount band drive the per-decision deduction
    # in the Complaints History factor (Annex One §6).
    op.execute(
        "CREATE TYPE leo_severity AS ENUM "
        "('limited_action','financial_award','rectification','apology','no_action')"
    )

    op.create_table(
        "complaints_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision_id", sa.String(50), nullable=True),
        sa.Column("decision_date", sa.Date(), nullable=True),
        sa.Column("remedy_type", sa.String(100), nullable=True),
        # Severity band (1 = most severe, 5 = least), per Annex One §6.10–§6.14.
        sa.Column("severity_band", sa.Integer(), nullable=False),
        sa.Column("severity_score", sa.Float(), nullable=False),
        # Remedy amount in £ and resulting score band (5 highest → 1 lowest).
        sa.Column("remedy_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("remedy_amount_score", sa.Float(), nullable=False),
        # Penalty when the firm's complaint handling is unreasonable (Annex One §6.16).
        sa.Column(
            "complaint_handling_penalty",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_complaints_decisions_org_id", "complaints_decisions", ["org_id"])

    # ── regulatory_decisions (SRA + SDT) ─────────────────────────────────────
    op.execute("CREATE TYPE regulatory_source AS ENUM ('sra','sdt')")
    op.execute(
        "CREATE TYPE sra_decision_type AS ENUM ("
        "'rebuke','fine_band_a','fine_band_b','fine_band_c','fine_band_d',"
        "'control_order','disqualification','strike_off','intervention')"
    )

    op.create_table(
        "regulatory_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "source",
            postgresql.ENUM("sra", "sdt", name="regulatory_source", create_type=False),
            nullable=False,
        ),
        sa.Column("decision_id", sa.String(50), nullable=True),
        sa.Column("decision_date", sa.Date(), nullable=True),
        sa.Column(
            "decision_type",
            postgresql.ENUM(
                "rebuke",
                "fine_band_a",
                "fine_band_b",
                "fine_band_c",
                "fine_band_d",
                "control_order",
                "disqualification",
                "strike_off",
                "intervention",
                name="sra_decision_type",
                create_type=False,
            ),
            nullable=False,
        ),
        # Pre-computed deduction for the Regulatory History factor (Annex One §7).
        sa.Column("deduction", sa.Float(), nullable=False),
        # SDT fines are banded by amount (Annex One §7.5).
        sa.Column("sdt_fine_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_regulatory_decisions_org_id", "regulatory_decisions", ["org_id"])
    op.create_index(
        "ix_regulatory_decisions_decision_type",
        "regulatory_decisions",
        ["decision_type"],
    )

    # ── analytics_events ─────────────────────────────────────────────────────
    op.create_table(
        "analytics_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analytics_events_session_id", "analytics_events", ["session_id"])
    op.create_index("ix_analytics_events_event_type", "analytics_events", ["event_type"])
    op.create_index("ix_analytics_events_created_at", "analytics_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("analytics_events")
    op.drop_table("regulatory_decisions")
    op.execute("DROP TYPE IF EXISTS sra_decision_type")
    op.execute("DROP TYPE IF EXISTS regulatory_source")
    op.drop_table("complaints_decisions")
    op.execute("DROP TYPE IF EXISTS leo_severity")
    op.drop_table("firm_users")
    op.execute("DROP TYPE IF EXISTS firm_user_role")
    op.drop_table("review_invitations")
    op.drop_table("reviews")
    op.execute("DROP TYPE IF EXISTS review_source")
    op.drop_table("appointments")
    op.execute("DROP TYPE IF EXISTS conflict_check_outcome")
    op.execute("DROP TYPE IF EXISTS appointment_status")
    op.execute("DROP TYPE IF EXISTS appointment_type")
    op.drop_table("chat_sessions")
    op.execute("DROP TYPE IF EXISTS scorecard_preference")
    op.drop_table("price_cards")
    op.drop_table("offices")
    op.drop_table("organisations")
