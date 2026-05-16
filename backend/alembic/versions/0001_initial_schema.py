"""Initial schema — conveyancing pilot (residential conveyancing, WMCA).

Schema is aligned to the Master Export workbook (Firms / Reputation / Price /
Complaints history / Regulatory history / Distance / Number of offices tabs).
Reputation, complaints and regulatory scores arrive pre-computed; the
runtime ranker consumes them directly.

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
        sa.Column("cml_firm_id", sa.String(10), nullable=False),
        sa.Column("sra_number", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("trading_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("referral_email", sa.String(255), nullable=True),
        sa.Column("excluded", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("exclusion_reason", sa.Text(), nullable=True),
        sa.Column("conveyancing_confirmed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "transparency_statement_captured",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("enrolled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("proceed_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("callback_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("active_in_pilot", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("enrollment_token", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("enrollment_token_used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("google_rating", sa.Float(), nullable=True),
        sa.Column("google_review_count", sa.Integer(), nullable=True),
        sa.Column("google_reviews_url", sa.String(500), nullable=True),
        sa.Column("adjusted_reputation_value", sa.Float(), nullable=True),
        sa.Column("master_export_updated_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("cml_firm_id"),
        sa.UniqueConstraint("sra_number"),
        sa.UniqueConstraint("enrollment_token"),
    )
    op.create_index("ix_organisations_cml_firm_id", "organisations", ["cml_firm_id"])
    op.create_index("ix_organisations_sra_number", "organisations", ["sra_number"])
    op.create_index("ix_organisations_enrolled", "organisations", ["enrolled"])
    op.create_index("ix_organisations_excluded", "organisations", ["excluded"])

    # ── offices ──────────────────────────────────────────────────────────────
    op.execute("CREATE TYPE office_type AS ENUM ('BRANCH', 'HO')")

    op.create_table(
        "offices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("address_line1", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("postcode", sa.String(10), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "office_type",
            postgresql.ENUM("BRANCH", "HO", name="office_type", create_type=False),
            nullable=True,
        ),
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
    op.execute("CREATE TYPE price_type AS ENUM ('estimated', 'verified', 'no_data')")

    op.create_table(
        "price_cards",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "price_type",
            postgresql.ENUM(
                "estimated", "verified", "no_data", name="price_type", create_type=False
            ),
            nullable=False,
            server_default="no_data",
        ),
        sa.Column(
            "pricing", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
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
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("org_id"),
    )
    op.create_index("ix_price_cards_org_id", "price_cards", ["org_id"])

    # ── chat_sessions ────────────────────────────────────────────────────────
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
        sa.Column("firm_contact_made", sa.Boolean(), nullable=True),
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

    # ── complaints_summary (pre-computed from Master Export) ────────────────
    op.create_table(
        "complaints_summary",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("display_text", sa.String(255), nullable=False),
        sa.Column("decision_count_text", sa.String(255), nullable=True),
        sa.Column("scale_context", sa.String(255), nullable=True),
        sa.Column("issue_one", sa.String(255), nullable=True),
        sa.Column("issue_two", sa.String(255), nullable=True),
        sa.Column("issue_three", sa.String(255), nullable=True),
        sa.Column("external_url", sa.String(500), nullable=True),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("org_id"),
    )

    # ── regulatory_summary (pre-computed from Master Export) ────────────────
    op.create_table(
        "regulatory_summary",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("display_text", sa.String(255), nullable=False),
        sa.Column("decision_count_text", sa.String(255), nullable=True),
        sa.Column("outcome_one", sa.String(255), nullable=True),
        sa.Column("outcome_two", sa.String(255), nullable=True),
        sa.Column("outcome_three", sa.String(255), nullable=True),
        sa.Column("external_url", sa.String(500), nullable=True),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("org_id"),
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
    op.drop_table("regulatory_summary")
    op.drop_table("complaints_summary")
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
    op.execute("DROP TYPE IF EXISTS price_type")
    op.drop_table("offices")
    op.execute("DROP TYPE IF EXISTS office_type")
    op.drop_table("organisations")
