"""Cloudflare R2 Object Storage integration using aioboto3."""

import uuid
from typing import Optional

import aioboto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings
from app.core.exceptions import BadRequestError, ServiceUnavailableError
from app.schemas.media import DirectUploadResponse, UploadResultResponse


def _r2_configured() -> bool:
    settings = get_settings()
    return bool(
        settings.cloudflare_account_id
        and settings.cloudflare_r2_access_key_id
        and settings.cloudflare_r2_secret_access_key
        and settings.cloudflare_r2_bucket_name
    )


def _get_s3_client_kwargs() -> dict:
    settings = get_settings()
    return {
        "service_name": "s3",
        "endpoint_url": f"https://{settings.cloudflare_account_id}.r2.cloudflarestorage.com",
        "aws_access_key_id": settings.cloudflare_r2_access_key_id,
        "aws_secret_access_key": settings.cloudflare_r2_secret_access_key,
        "region_name": "auto",
    }


def build_public_url(key: str) -> str:
    """Build the public delivery URL for an object in Cloudflare R2."""
    settings = get_settings()
    base_url = settings.cloudflare_r2_public_domain.rstrip("/")
    return f"{base_url}/{key}"


async def create_direct_upload_url(
    filename: str = "poster.jpg",
    content_type: str = "image/jpeg",
    expires_in: int = 3600,
) -> DirectUploadResponse:
    """Generate a presigned PUT URL for direct client-side upload to R2."""
    if not _r2_configured():
        raise ServiceUnavailableError("Cloudflare R2 is not properly configured.")

    settings = get_settings()
    unique_key = f"posters/{uuid.uuid4().hex}_{filename}"

    try:
        session = aioboto3.Session()
        async with session.client(**_get_s3_client_kwargs()) as s3_client:
            presigned_url = await s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": settings.cloudflare_r2_bucket_name,
                    "Key": unique_key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
            )
    except (BotoCoreError, ClientError) as exc:
        raise ServiceUnavailableError(f"Failed to generate R2 upload URL: {exc}") from exc

    return DirectUploadResponse(
        upload_url=presigned_url,
        image_id=unique_key,
        public_url=build_public_url(unique_key),
    )


async def upload_image_bytes(
    content: bytes,
    *,
    filename: str = "poster.jpg",
    content_type: str = "image/jpeg",
) -> UploadResultResponse:
    """Upload raw image bytes directly from backend to R2."""
    if not _r2_configured():
        raise ServiceUnavailableError("Cloudflare R2 is not properly configured.")
    if not content:
        raise BadRequestError("Empty image payload")

    settings = get_settings()
    unique_key = f"posters/{uuid.uuid4().hex}_{filename}"

    try:
        session = aioboto3.Session()
        async with session.client(**_get_s3_client_kwargs()) as s3_client:
            await s3_client.put_object(
                Bucket=settings.cloudflare_r2_bucket_name,
                Key=unique_key,
                Body=content,
                ContentType=content_type,
            )
    except (BotoCoreError, ClientError) as exc:
        raise ServiceUnavailableError(f"Failed to upload image to R2: {exc}") from exc

    public_url = build_public_url(unique_key)
    return UploadResultResponse(
        image_id=unique_key,
        public_url=public_url,
        variants=[public_url],
    )