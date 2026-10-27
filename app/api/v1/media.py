"""Cloudflare Images media upload endpoints."""

from typing import Optional

from fastapi import APIRouter, File, UploadFile, status

from app.core.dependencies import CurrentNGO
from app.schemas.media import (
    DirectUploadRequest,
    DirectUploadResponse,
    UploadResultResponse,
)
from app.services import cloudflare as cloudflare_service

router = APIRouter(prefix="/media", tags=["Media"])


@router.post(
    "/upload-url",
    response_model=DirectUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Cloudflare Images direct upload URL",
)
async def create_upload_url(
    current_user: CurrentNGO,
    payload: Optional[DirectUploadRequest] = None,
) -> DirectUploadResponse:
    """Generate a one-time Cloudflare direct upload URL.

    Client flow:
    1. Call this endpoint with a Bearer NGO token.
    2. `POST` the image binary to the returned `upload_url`.
    3. Persist `public_url` as the event `poster_url`.
    """
    _ = current_user  # auth gate
    return await cloudflare_service.create_direct_upload_url(payload)


@router.post(
    "/upload",
    response_model=UploadResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload image via server (multipart)",
)
async def upload_image(
    current_user: CurrentNGO,
    file: UploadFile = File(..., description="Image file (JPEG/PNG/WebP)"),
) -> UploadResultResponse:
    """Proxy a multipart image upload to Cloudflare Images.

    Prefer `/media/upload-url` for large files / client-side uploads.
    """
    _ = current_user
    content = await file.read()
    content_type = file.content_type or "application/octet-stream"
    filename = file.filename or "poster.jpg"
    return await cloudflare_service.upload_image_bytes(
        content,
        filename=filename,
        content_type=content_type,
    )
