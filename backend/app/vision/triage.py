"""Confidence-based triage — post-inference flagging.

Feature 3 from disease_recognition_scope.md:
  Flags low-confidence detections for review instead of
  presenting them as definitive diagnoses.
"""

import logging

from app.config import settings

logger = logging.getLogger(__name__)


def apply_triage(detections: list[dict]) -> tuple[list[dict], bool]:
    """Apply confidence triage to a list of detections.

    Adds `is_low_confidence` flag to each detection.
    Returns (updated_detections, needs_review).

    `needs_review` is True if ANY detection is below threshold.
    """
    threshold = settings.confidence_threshold
    needs_review = False

    for det in detections:
        confidence = det.get("confidence", 0.0)
        is_low = confidence < threshold
        det["is_low_confidence"] = is_low

        if is_low:
            needs_review = True
            logger.info(
                "Low confidence detection: %s (%.2f < %.2f) — flagged for review",
                det.get("disease", "unknown"),
                confidence,
                threshold,
            )

    return detections, needs_review
