"""Diagnosis router — image upload, quality gating, inference, and report storage.

Endpoints:
  POST /api/diagnosis/upload  — multipart upload → full pipeline → DiagnosisResponse
  GET  /api/diagnosis/{id}    — retrieve a single report by ID
  GET  /api/diagnosis/reports — list reports for current farmer (paginated)
"""

import logging
from uuid import UUID

import cv2
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import CropType, DiseaseReport, Farmer
from app.db.postgres import get_db
from app.dependencies import get_current_user, require_role
from app.schemas.diagnosis import (
    DetectionItem,
    DiagnosisListItem,
    DiagnosisResponse,
    QualityCheckResponse,
)
from app.storage import save_upload, UPLOAD_DIR
from app.vision.preprocess import check_image_quality
from app.vision.severity import estimate_severity
from app.vision.triage import apply_triage
from app.vision.yolo_inference import run_inference

logger = logging.getLogger(__name__)

router = APIRouter()

# Allowed image MIME types
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/jpg"}
MAX_UPLOAD_BYTES = settings.max_upload_size_mb * 1024 * 1024


@router.post(
    "/upload",
    response_model=DiagnosisResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("farmer"))],
    summary="Upload a crop image for disease diagnosis",
)
async def upload_diagnosis(
    file: UploadFile = File(..., description="Crop leaf/plant image (JPEG/PNG, max 10MB)"),
    crop_type: str = Form(..., description="One of: cotton, maize, soybean, sugarcane, wheat"),
    district: str = Form(default="Chh. Sambhajinagar", description="District name"),
    taluka: str = Form(default=None, description="Taluka name"),
    lat: float = Form(default=None, description="Latitude"),
    lng: float = Form(default=None, description="Longitude"),
    current_user: Farmer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Full diagnosis pipeline:
    1. Validate file type and size
    2. Save image to local storage
    3. Run image quality gating
    4. Run YOLOv8 inference (or stub)
    5. Estimate severity per detection
    6. Apply confidence triage
    7. Store DiseaseReport in Postgres
    8. Return full response
    """
    # --- 1. Validate file ---
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Only JPEG and PNG are accepted.",
        )

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large ({len(content) // (1024*1024)}MB). Maximum is {settings.max_upload_size_mb}MB.",
        )

    # Validate crop_type
    try:
        crop_enum = CropType(crop_type.lower())
    except ValueError:
        valid = [c.value for c in CropType]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid crop_type: '{crop_type}'. Must be one of: {valid}",
        )

    farmer_id_str = str(current_user.id)

    # --- 2. Save image ---
    image_url = save_upload(content, farmer_id_str, file.filename or "upload.jpg")
    image_full_path = str(UPLOAD_DIR.parent / image_url)

    # --- 3. Quality gating ---
    quality = check_image_quality(image_full_path)
    quality_response = QualityCheckResponse(
        passed=quality.passed,
        rejection_reason=quality.rejection_reason,
        blur_score=quality.blur_score,
        brightness=quality.brightness,
    )

    if not quality.passed:
        # Save report with quality failure — don't run inference
        report = DiseaseReport(
            farmer_id=current_user.id,
            crop_type=crop_enum,
            image_quality_passed=False,
            detections=None,
            needs_review=False,
            district=district,
            taluka=taluka,
            lat=lat,
            lng=lng,
            image_url=image_url,
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)

        return DiagnosisResponse(
            id=str(report.id),
            farmer_id=farmer_id_str,
            crop_type=crop_enum.value,
            image_url=image_url,
            image_quality_passed=False,
            quality_check=quality_response,
            detections=[],
            needs_review=False,
        )

    # --- 4. YOLOv8 inference ---
    inference_result = run_inference(image_full_path, crop_enum.value)
    stub_warning = None

    if not inference_result.success and not inference_result.detections:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=inference_result.error or "Inference failed",
        )

    # Check if this was a stub response
    if inference_result.error and "STUB" in inference_result.error:
        stub_warning = inference_result.error

    # --- 5. Severity estimation ---
    image = cv2.imread(image_full_path)
    img_h, img_w = image.shape[:2] if image is not None else (640, 640)

    detections_dicts = []
    for det in inference_result.detections:
        severity = estimate_severity(det.bbox, img_w, img_h)
        detections_dicts.append({
            "disease": det.disease,
            "confidence": det.confidence,
            "severity": severity,
            "bbox": det.bbox,
        })

    # --- 6. Confidence triage ---
    detections_dicts, needs_review = apply_triage(detections_dicts)

    # --- 7. Store report ---
    report = DiseaseReport(
        farmer_id=current_user.id,
        crop_type=crop_enum,
        image_quality_passed=True,
        detections=detections_dicts,
        needs_review=needs_review,
        district=district,
        taluka=taluka,
        lat=lat,
        lng=lng,
        image_url=image_url,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    # --- 8. Return response ---
    detection_items = [
        DetectionItem(
            disease=d["disease"],
            confidence=d["confidence"],
            severity=d["severity"],
            bbox=d["bbox"],
            is_low_confidence=d.get("is_low_confidence", False),
        )
        for d in detections_dicts
    ]

    return DiagnosisResponse(
        id=str(report.id),
        farmer_id=farmer_id_str,
        crop_type=crop_enum.value,
        image_url=image_url,
        image_quality_passed=True,
        quality_check=quality_response,
        detections=detection_items,
        needs_review=needs_review,
        district=district,
        taluka=taluka,
        stub_warning=stub_warning,
    )


@router.get(
    "/{report_id}",
    response_model=DiagnosisResponse,
    summary="Get a diagnosis report by ID",
)
async def get_diagnosis(
    report_id: UUID,
    current_user: Farmer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single diagnosis report. Farmers can only see their own."""
    result = await db.execute(
        select(DiseaseReport).where(DiseaseReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    # Farmers can only view their own reports
    if str(report.farmer_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own reports",
        )

    detections = report.detections or []
    detection_items = [
        DetectionItem(
            disease=d["disease"],
            confidence=d["confidence"],
            severity=d.get("severity", "mild"),
            bbox=d["bbox"],
            is_low_confidence=d.get("is_low_confidence", False),
        )
        for d in detections
    ]

    return DiagnosisResponse(
        id=str(report.id),
        farmer_id=str(report.farmer_id),
        crop_type=report.crop_type.value if hasattr(report.crop_type, "value") else report.crop_type,
        image_url=report.image_url,
        image_quality_passed=report.image_quality_passed or False,
        detections=detection_items,
        needs_review=report.needs_review,
        district=report.district,
        taluka=report.taluka,
    )


@router.get(
    "/reports/me",
    response_model=list[DiagnosisListItem],
    summary="List diagnosis reports for the current farmer",
)
async def list_my_reports(
    skip: int = 0,
    limit: int = 20,
    current_user: Farmer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Paginated list of the current farmer's diagnosis reports."""
    result = await db.execute(
        select(DiseaseReport)
        .where(DiseaseReport.farmer_id == current_user.id)
        .order_by(DiseaseReport.reported_at.desc())
        .offset(skip)
        .limit(limit)
    )
    reports = result.scalars().all()

    return [
        DiagnosisListItem(
            id=str(r.id),
            crop_type=r.crop_type.value if hasattr(r.crop_type, "value") else r.crop_type,
            detections_count=len(r.detections) if r.detections else 0,
            needs_review=r.needs_review,
            image_quality_passed=r.image_quality_passed or False,
            reported_at=r.reported_at.isoformat() if r.reported_at else None,
        )
        for r in reports
    ]
