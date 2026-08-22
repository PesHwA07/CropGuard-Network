"""Severity estimation — post-inference processing.

Feature 1 from disease_recognition_scope.md:
  Calculates infected-area ratio from bounding boxes and maps
  to severity levels: mild / moderate / severe.
"""

import logging

logger = logging.getLogger(__name__)

# Severity thresholds (fraction of total image area)
MILD_UPPER = 0.10       # < 10% → mild
MODERATE_UPPER = 0.30   # 10-30% → moderate
                         # > 30% → severe


def estimate_severity(
    bbox: list[float],
    image_width: int,
    image_height: int,
) -> str:
    """Estimate disease severity from a single detection bbox.

    Args:
        bbox: [x1, y1, x2, y2] pixel coordinates
        image_width: original image width in pixels
        image_height: original image height in pixels

    Returns:
        "mild", "moderate", or "severe"
    """
    total_area = image_width * image_height
    if total_area == 0:
        return "mild"

    x1, y1, x2, y2 = bbox
    bbox_area = abs(x2 - x1) * abs(y2 - y1)
    ratio = bbox_area / total_area

    if ratio < MILD_UPPER:
        severity = "mild"
    elif ratio < MODERATE_UPPER:
        severity = "moderate"
    else:
        severity = "severe"

    logger.debug(
        "Severity: bbox_area=%.0f total=%.0f ratio=%.3f → %s",
        bbox_area, total_area, ratio, severity,
    )
    return severity


def attach_severity_to_detections(
    detections: list[dict],
    image_width: int,
    image_height: int,
) -> list[dict]:
    """Add severity field to each detection dict.

    Modifies detections in-place and returns them.
    """
    for det in detections:
        det["severity"] = estimate_severity(
            det["bbox"], image_width, image_height,
        )
    return detections
