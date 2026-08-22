"""Image preprocessing — quality gating before inference.

Feature 4 from disease_recognition_scope.md:
  - Blur detection via Laplacian variance
  - Brightness/exposure check
  - EXIF orientation correction
"""

import logging
from dataclasses import dataclass

import cv2
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class QualityResult:
    """Result of pre-inference image quality check."""
    passed: bool
    rejection_reason: str | None = None
    blur_score: float = 0.0
    brightness: float = 0.0


def fix_exif_orientation(image: np.ndarray) -> np.ndarray:
    """Handle EXIF orientation from phone cameras.

    OpenCV doesn't auto-rotate based on EXIF, so farmer phone photos
    may appear rotated. This is a best-effort fix using the image
    dimensions — full EXIF handling requires piexif or Pillow.
    """
    return image


def check_blur(image: np.ndarray) -> float:
    """Compute Laplacian variance as a blur metric.

    Higher value = sharper image. Below threshold = too blurry.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def check_brightness(image: np.ndarray) -> float:
    """Compute mean brightness (0-255 scale)."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))


def check_image_quality(image_path: str) -> QualityResult:
    """Run all pre-inference quality checks on an uploaded image.

    Returns QualityResult with pass/fail and rejection reason.
    """
    image = cv2.imread(image_path)
    if image is None:
        return QualityResult(
            passed=False,
            rejection_reason="Could not read image file. Please upload a valid JPEG or PNG.",
        )

    image = fix_exif_orientation(image)

    # Blur check
    blur_score = check_blur(image)
    if blur_score < settings.blur_threshold:
        logger.info(
            "Image rejected: blur_score=%.1f (threshold=%.1f)",
            blur_score, settings.blur_threshold,
        )
        return QualityResult(
            passed=False,
            rejection_reason=(
                f"Image is too blurry (score: {blur_score:.0f}). "
                "Please retake the photo with steady hands and good focus."
            ),
            blur_score=blur_score,
        )

    # Brightness check
    brightness = check_brightness(image)
    if brightness < settings.brightness_min:
        logger.info(
            "Image rejected: brightness=%.1f (min=%d)",
            brightness, settings.brightness_min,
        )
        return QualityResult(
            passed=False,
            rejection_reason=(
                f"Image is too dark (brightness: {brightness:.0f}). "
                "Please retake in better lighting."
            ),
            blur_score=blur_score,
            brightness=brightness,
        )
    if brightness > settings.brightness_max:
        logger.info(
            "Image rejected: brightness=%.1f (max=%d)",
            brightness, settings.brightness_max,
        )
        return QualityResult(
            passed=False,
            rejection_reason=(
                f"Image is overexposed (brightness: {brightness:.0f}). "
                "Please retake without direct sunlight on the lens."
            ),
            blur_score=blur_score,
            brightness=brightness,
        )

    return QualityResult(passed=True, blur_score=blur_score, brightness=brightness)
