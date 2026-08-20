"""Initial schema: farmers, disease_reports, shops, shop_stock

Revision ID: 0001
Revises: None
Create Date: 2026-08-19

Updated 2026-08-20: disease_reports schema changed per disease_recognition_scope.md
  - Replaced disease_detected (String) + confidence_score (Float)
    with detections (JSONB), needs_review (Boolean), image_quality_passed (Boolean)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Enums ---
    role_enum = sa.Enum(
        "farmer", "shop_owner", "extension_officer", name="role", schema=None
    )
    crop_enum = sa.Enum(
        "maize", "soybean", "sugarcane", "cotton", "wheat", name="croptype", schema=None
    )
    role_enum.create(op.get_bind(), checkfirst=True)
    crop_enum.create(op.get_bind(), checkfirst=True)

    # --- farmers ---
    op.create_table(
        "farmers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("district", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_farmers_email", "farmers", ["email"])

    # --- disease_reports ---
    # Schema per disease_recognition_scope.md:
    #   detections = JSONB list of {disease, confidence, severity, bbox}
    #   needs_review = True when any detection below confidence threshold
    #   image_quality_passed = False when pre-inference gating rejects image
    op.create_table(
        "disease_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "farmer_id",
            UUID(as_uuid=True),
            sa.ForeignKey("farmers.id"),
            nullable=False,
        ),
        sa.Column("crop_type", crop_enum, nullable=False),
        sa.Column("detections", JSONB, nullable=True),
        sa.Column(
            "needs_review", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("image_quality_passed", sa.Boolean(), nullable=True),
        sa.Column("district", sa.String(), nullable=True),
        sa.Column("taluka", sa.String(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("reported_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_disease_reports_district", "disease_reports", ["district"])
    op.create_index("ix_disease_reports_taluka", "disease_reports", ["taluka"])
    op.create_index("ix_disease_reports_crop_type", "disease_reports", ["crop_type"])

    # --- shops ---
    op.create_table(
        "shops",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            UUID(as_uuid=True),
            sa.ForeignKey("farmers.id"),
            nullable=True,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("district", sa.String(), nullable=False),
        sa.Column("taluka", sa.String(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # --- shop_stock ---
    op.create_table(
        "shop_stock",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "shop_id",
            UUID(as_uuid=True),
            sa.ForeignKey("shops.id"),
            nullable=False,
        ),
        sa.Column("pesticide_name", sa.String(), nullable=False),
        sa.Column(
            "quantity_available",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("shop_stock")
    op.drop_table("shops")
    op.drop_table("disease_reports")
    op.drop_table("farmers")
    sa.Enum(name="croptype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="role").drop(op.get_bind(), checkfirst=True)
