"""Local file storage for uploaded crop images.

Saves to backend/uploads/{farmer_id}/{uuid}.{ext}.
Swappable for Azure Blob Storage later without API changes.
"""

import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


def save_upload(
    file_content: bytes,
    farmer_id: str,
    original_filename: str,
) -> str:
    """Save uploaded image to local filesystem.

    Args:
        file_content: raw image bytes
        farmer_id: UUID string of the uploading farmer
        original_filename: original filename for extension extraction

    Returns:
        Relative path string for storage in image_url field
    """
    ext = Path(original_filename).suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        ext = ".jpg"

    unique_name = f"{uuid.uuid4()}{ext}"
    farmer_dir = UPLOAD_DIR / farmer_id
    farmer_dir.mkdir(parents=True, exist_ok=True)

    file_path = farmer_dir / unique_name
    file_path.write_bytes(file_content)

    relative_path = f"uploads/{farmer_id}/{unique_name}"
    logger.info("Saved upload: %s (%d bytes)", relative_path, len(file_content))
    return relative_path
