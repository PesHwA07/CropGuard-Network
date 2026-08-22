"""YOLOv8 inference service for crop disease detection.

Loads crop-specific .pt models from settings.yolo_model_dir.
Returns all detections (multi-disease support per Feature 2).

Until trained models are available from Colab, this module returns
a stub response so the full pipeline can be tested end-to-end.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Single detection from YOLOv8 inference."""
    disease: str
    confidence: float
    bbox: list[float]  # [x1, y1, x2, y2] pixel coordinates


@dataclass
class InferenceResult:
    """Complete inference result for one image."""
    success: bool
    detections: list[Detection] = field(default_factory=list)
    error: str | None = None
    model_path: str | None = None


def _get_model_path(crop_type: str) -> Path:
    """Resolve the .pt model file for a given crop type."""
    return Path(settings.yolo_model_dir) / crop_type / "best.pt"


def run_inference(image_path: str, crop_type: str) -> InferenceResult:
    """Run YOLOv8 inference on a preprocessed image.

    Loads the crop-specific model and returns ALL detections
    (not just top-1) to support multi-disease detection.
    """
    model_path = _get_model_path(crop_type)

    if not model_path.exists():
        logger.warning(
            "No trained model found at %s — returning stub response",
            model_path,
        )
        return _stub_inference(image_path, crop_type)

    try:
        from ultralytics import YOLO

        model = YOLO(str(model_path))
        results = model.predict(
            source=image_path,
            conf=0.25,  # low threshold to catch all detections
            verbose=False,
        )

        detections = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                cls_name = result.names[cls_id]
                conf = float(box.conf[0])
                bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                detections.append(Detection(
                    disease=cls_name,
                    confidence=round(conf, 4),
                    bbox=[round(c, 1) for c in bbox],
                ))

        logger.info(
            "Inference complete: %d detections from %s model",
            len(detections), crop_type,
        )
        return InferenceResult(
            success=True,
            detections=detections,
            model_path=str(model_path),
        )

    except Exception as e:
        logger.error("Inference failed: %s", str(e))
        return InferenceResult(
            success=False,
            error=f"Model inference failed: {str(e)}",
            model_path=str(model_path),
        )


def _stub_inference(image_path: str, crop_type: str) -> InferenceResult:
    """Return mock detections when no trained model is available.

    Uses cotton disease classes per the implementation plan.
    This stub is replaced once real .pt models are trained on Colab.
    """
    import cv2

    image = cv2.imread(image_path)
    if image is None:
        return InferenceResult(success=False, error="Could not read image for stub inference")

    h, w = image.shape[:2]

    # Cotton-specific stub detections
    stub_detections = {
        "cotton": [
            Detection(
                disease="bacterial_blight",
                confidence=0.82,
                bbox=[w * 0.1, h * 0.15, w * 0.45, h * 0.55],
            ),
        ],
        "maize": [
            Detection(
                disease="common_rust",
                confidence=0.78,
                bbox=[w * 0.2, h * 0.1, w * 0.6, h * 0.5],
            ),
        ],
        "soybean": [
            Detection(
                disease="leaf_spot",
                confidence=0.75,
                bbox=[w * 0.15, h * 0.2, w * 0.5, h * 0.6],
            ),
        ],
    }

    detections = stub_detections.get(crop_type, [
        Detection(
            disease="unknown_disease",
            confidence=0.65,
            bbox=[w * 0.1, h * 0.1, w * 0.5, h * 0.5],
        ),
    ])

    logger.info("Stub inference: returning %d mock detections for %s", len(detections), crop_type)
    return InferenceResult(
        success=True,
        detections=detections,
        error="STUB: No trained model found. Using mock detections.",
    )
