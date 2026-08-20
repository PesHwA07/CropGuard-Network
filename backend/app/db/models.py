"""SQLAlchemy ORM models for CropGuard Network.

Tables: farmers, disease_reports, shops, shop_stock
Enums:  Role (3 roles), CropType (5 Sambhajinagar-region crops)

Schema reflects disease_recognition_scope.md:
  - detections stored as JSONB (multi-disease per image)
  - needs_review flag for low-confidence triage
  - image_quality_passed flag for pre-inference gating
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, relationship


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Role(str, enum.Enum):
    """Auth roles per scope decision #5."""
    FARMER = "farmer"
    SHOP_OWNER = "shop_owner"
    EXTENSION_OFFICER = "extension_officer"


class CropType(str, enum.Enum):
    """v1 crops for Chh. Sambhajinagar district."""
    MAIZE = "maize"
    SOYBEAN = "soybean"
    SUGARCANE = "sugarcane"
    COTTON = "cotton"
    WHEAT = "wheat"


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(SQLEnum(Role, values_callable=lambda e: [m.value for m in e]), nullable=False)
    district = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    reports = relationship("DiseaseReport", back_populates="farmer")
    shops = relationship("Shop", back_populates="owner")


class DiseaseReport(Base):
    """One report per uploaded image.

    `detections` is a JSONB list of objects, each containing:
        {
            "disease": "common_rust",
            "confidence": 0.87,
            "severity": "moderate",   # mild | moderate | severe
            "bbox": [x1, y1, x2, y2]  # pixel coordinates
        }
    Supports multi-disease detection (Feature 2) and severity estimation
    (Feature 1) from disease_recognition_scope.md.
    """
    __tablename__ = "disease_reports"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("farmers.id"), nullable=False
    )
    crop_type = Column(SQLEnum(CropType, values_callable=lambda e: [m.value for m in e]), nullable=False)

    # Multi-disease detections stored as JSONB array
    detections = Column(JSONB, nullable=True)

    # Confidence-based triage (Feature 3)
    needs_review = Column(Boolean, nullable=False, server_default="false")

    # Image quality gating (Feature 4)
    image_quality_passed = Column(Boolean, nullable=True)

    district = Column(String, nullable=True, index=True)
    taluka = Column(String, nullable=True, index=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    image_url = Column(String, nullable=True)
    reported_at = Column(DateTime, server_default=func.now())

    farmer = relationship("Farmer", back_populates="reports")


class Shop(Base):
    __tablename__ = "shops"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("farmers.id"), nullable=True
    )
    name = Column(String, nullable=False)
    district = Column(String, nullable=False)
    taluka = Column(String, nullable=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    owner = relationship("Farmer", back_populates="shops")
    stock_items = relationship("ShopStock", back_populates="shop")


class ShopStock(Base):
    __tablename__ = "shop_stock"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("shops.id"), nullable=False
    )
    pesticide_name = Column(String, nullable=False)
    quantity_available = Column(Integer, nullable=False, server_default="0")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    shop = relationship("Shop", back_populates="stock_items")
