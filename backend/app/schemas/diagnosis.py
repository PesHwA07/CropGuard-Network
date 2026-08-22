"""Pydantic schemas for the diagnosis pipeline."""

from pydantic import BaseModel, Field


class DetectionItem(BaseModel):
    """Single disease detection within a diagnosis report."""
    disease: str
    confidence: float = Field(ge=0.0, le=1.0)
    severity: str = Field(description="mild | moderate | severe")
    bbox: list[float] = Field(description="[x1, y1, x2, y2] pixel coordinates")
    is_low_confidence: bool = False


class QualityCheckResponse(BaseModel):
    """Image quality gating result."""
    passed: bool
    rejection_reason: str | None = None
    blur_score: float = 0.0
    brightness: float = 0.0


class DiagnosisResponse(BaseModel):
    """Full diagnosis report returned to the farmer."""
    id: str
    farmer_id: str
    crop_type: str
    image_url: str | None = None
    image_quality_passed: bool
    quality_check: QualityCheckResponse | None = None
    detections: list[DetectionItem] = []
    needs_review: bool = False
    district: str | None = None
    taluka: str | None = None
    stub_warning: str | None = Field(
        default=None,
        description="Present when using stub inference (no trained model)",
    )


class DiagnosisListItem(BaseModel):
    """Compact view for listing a farmer's reports."""
    id: str
    crop_type: str
    detections_count: int
    needs_review: bool
    image_quality_passed: bool
    reported_at: str | None = None
