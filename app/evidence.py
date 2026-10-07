"""Evidence scrubbing, storage, and file deletion utilities."""

from io import BytesIO
from pathlib import Path
from typing import Optional
import uuid

from fastapi import HTTPException
from PIL import Image

UPLOAD_DIR = Path("uploads")
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def get_upload_dir() -> Path:
    """Return the configured upload directory, honoring any test monkeypatching."""
    import app.routes

    return Path(getattr(app.routes, "UPLOAD_DIR", UPLOAD_DIR))


def scrub_image(contents: bytes, content_type: str) -> tuple[bytes, str]:
    """Validate and strip EXIF/GPS metadata from image bytes in-memory.

    Returns the cleaned image bytes and normalized extension.
    Raises HTTPException on validation or processing failure.
    """
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{content_type}'. Allowed: JPEG, PNG, WebP.",
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )

    try:
        image = Image.open(BytesIO(contents))
        image.load()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file.")

    img_format = image.format or "PNG"
    save_image: Image.Image = image
    if img_format == "JPEG" and image.mode in ("RGBA", "LA", "P"):
        save_image = image.convert("RGB")

    clean_buffer = BytesIO()
    save_image.save(clean_buffer, format=img_format)
    clean_data = clean_buffer.getvalue()

    ext = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}.get(img_format, ".png")
    return clean_data, ext


def save_evidence(clean_data: bytes, ext: str) -> str:
    """Save scrubbed evidence data to disk and return the public URL path."""
    upload_dir = get_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}{ext}"
    filepath = upload_dir / filename
    filepath.write_bytes(clean_data)

    return f"/uploads/{filename}"


def delete_evidence(evidence_url: Optional[str]) -> bool:
    """Delete evidence file associated with an evidence URL if it exists on disk.

    Supports ADR-0002 permanent case closure data minimization.
    """
    if not evidence_url:
        return False

    filename = Path(evidence_url).name
    filepath = get_upload_dir() / filename
    if filepath.exists() and filepath.is_file():
        filepath.unlink(missing_ok=True)
        return True
    return False
