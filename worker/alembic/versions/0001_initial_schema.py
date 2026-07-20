"""initial schema: reports, extractions, anomalies, reviews, spec_profiles

Revision ID: 0001
Revises:
Create Date: 2026-07-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("report_type", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="uploaded"),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "extractions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "report_id",
            sa.Uuid(),
            sa.ForeignKey("reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("schema_version", sa.String(), nullable=False),
        sa.Column(
            "data", sa.JSON().with_variant(JSONB(), "postgresql"), nullable=False
        ),
        sa.Column(
            "confidence", sa.JSON().with_variant(JSONB(), "postgresql"), nullable=False
        ),
        sa.Column(
            "validation_errors",
            sa.JSON().with_variant(JSONB(), "postgresql"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_extractions_report_id", "extractions", ["report_id"])

    op.create_table(
        "anomalies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "report_id",
            sa.Uuid(),
            sa.ForeignKey("reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("field", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=True),
        sa.Column("expected_range", sa.String(), nullable=True),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_anomalies_report_id", "anomalies", ["report_id"])

    op.create_table(
        "reviews",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "report_id",
            sa.Uuid(),
            sa.ForeignKey("reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_edits",
            sa.JSON().with_variant(JSONB(), "postgresql"),
            nullable=False,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_reviews_report_id", "reviews", ["report_id"])

    op.create_table(
        "spec_profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("report_type", sa.String(), nullable=False),
        sa.Column("field", sa.String(), nullable=False),
        sa.Column("min_value", sa.Numeric(), nullable=True),
        sa.Column("max_value", sa.Numeric(), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.UniqueConstraint("report_type", "field", name="uq_spec_profiles_type_field"),
    )
    op.create_index("ix_spec_profiles_report_type", "spec_profiles", ["report_type"])


def downgrade() -> None:
    op.drop_table("spec_profiles")
    op.drop_table("reviews")
    op.drop_table("anomalies")
    op.drop_table("extractions")
    op.drop_table("reports")
