"""Evidence upload and metadata scrubbing routes."""

from fastapi import APIRouter, UploadFile

from app.evidence import save_evidence, scrub_image
from app.schemas import EvidenceUploaded

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("/upload", response_model=EvidenceUploaded, status_code=201)
async def upload_evidence(file: UploadFile):
    """Upload an image file with automatic EXIF/GPS metadata stripping.

    Accepts JPEG, PNG, and WebP up to 5 MB.
    """
    contents = await file.read()
    clean_data, ext = scrub_image(contents, file.content_type or "")
    url = save_evidence(clean_data, ext)
    return EvidenceUploaded(url=url)
