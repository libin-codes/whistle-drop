"""Tests for POST /api/v1/evidence/upload — evidence upload & EXIF scrubbing (AC 4-5)."""

import io

import pytest
from PIL import Image
from PIL.ExifTags import Base as ExifBase


def _make_image_bytes(
    fmt: str = "JPEG",
    size: tuple[int, int] = (100, 100),
    exif: bool = True,
) -> bytes:
    """Create a minimal image with optional EXIF metadata."""
    img = Image.new("RGB", size, color="red")

    buf = io.BytesIO()
    if exif and fmt == "JPEG":
        # Inject EXIF data (Make and Model tags)
        exif_data = img.getexif()
        exif_data[ExifBase.Make] = "TestCamera"
        exif_data[ExifBase.Model] = "TestModel"
        exif_data[ExifBase.Software] = "TestSoftware"
        img.save(buf, format=fmt, exif=exif_data.tobytes())
    else:
        img.save(buf, format=fmt)

    return buf.getvalue()


def _content_type(fmt: str) -> str:
    return {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}[fmt]


@pytest.mark.asyncio
async def test_upload_jpeg_strips_exif(client, tmp_path):
    """JPEG upload strips EXIF metadata and returns a scrubbed file URL."""
    data = _make_image_bytes("JPEG", exif=True)

    resp = await client.post(
        "/api/v1/evidence/upload",
        files={"file": ("photo.jpg", data, "image/jpeg")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["url"].startswith("/uploads/")
    assert body["url"].endswith(".jpg")

    # Verify the saved file has no EXIF
    saved_path = tmp_path / body["url"].split("/")[-1]
    saved_img = Image.open(saved_path)
    exif = saved_img.getexif()
    assert ExifBase.Make not in exif
    assert ExifBase.Model not in exif
    assert ExifBase.Software not in exif


@pytest.mark.asyncio
async def test_upload_png(client):
    """PNG upload succeeds."""
    data = _make_image_bytes("PNG")
    resp = await client.post(
        "/api/v1/evidence/upload",
        files={"file": ("screenshot.png", data, "image/png")},
    )
    assert resp.status_code == 201
    assert resp.json()["url"].endswith(".png")


@pytest.mark.asyncio
async def test_upload_webp(client):
    """WebP upload succeeds."""
    data = _make_image_bytes("WEBP")
    resp = await client.post(
        "/api/v1/evidence/upload",
        files={"file": ("image.webp", data, "image/webp")},
    )
    assert resp.status_code == 201
    assert resp.json()["url"].endswith(".webp")


@pytest.mark.asyncio
async def test_upload_unsupported_type_returns_415(client):
    """Non-image file types are rejected with 415."""
    resp = await client.post(
        "/api/v1/evidence/upload",
        files={"file": ("doc.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert resp.status_code == 415


@pytest.mark.asyncio
async def test_upload_oversized_file_returns_400(client):
    """Files exceeding 5 MB are rejected with 400."""
    # 6 MB of zeros
    oversized = b"\x00" * (6 * 1024 * 1024)
    resp = await client.post(
        "/api/v1/evidence/upload",
        files={"file": ("huge.jpg", oversized, "image/jpeg")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_upload_uuid_filename(client):
    """Saved file uses a UUID filename, not the original."""
    import re

    data = _make_image_bytes("JPEG")
    resp = await client.post(
        "/api/v1/evidence/upload",
        files={"file": ("my_secret_photo.jpg", data, "image/jpeg")},
    )
    url = resp.json()["url"]
    filename = url.split("/")[-1]
    # Must be a UUID4 + extension
    name_part = filename.rsplit(".", 1)[0]
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        name_part,
    )


@pytest.mark.asyncio
async def test_upload_corrupted_image_returns_400(client):
    """Corrupted image payload claiming to be JPEG returns 400."""
    resp = await client.post(
        "/api/v1/evidence/upload",
        files={"file": ("corrupt.jpg", b"not-a-real-jpeg-image-bytes", "image/jpeg")},
    )
    assert resp.status_code == 400
    assert "Invalid image file" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_delete_evidence_removes_file(client, tmp_path):
    """delete_evidence unlinks the uploaded file from disk."""
    from app.evidence import delete_evidence

    data = _make_image_bytes("JPEG")
    resp = await client.post(
        "/api/v1/evidence/upload",
        files={"file": ("to_delete.jpg", data, "image/jpeg")},
    )
    url = resp.json()["url"]
    filename = url.split("/")[-1]
    filepath = tmp_path / filename
    assert filepath.exists()

    result = delete_evidence(url)
    assert result is True
    assert not filepath.exists()

    # Deleting non-existent file returns False gracefully
    assert delete_evidence(url) is False
    assert delete_evidence(None) is False

