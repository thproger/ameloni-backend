"""Cloudflare Images / media upload schemas."""

from typing import Optional

from pydantic import BaseModel, Field


class DirectUploadRequest(BaseModel):
    """Optional metadata when requesting a Cloudflare direct upload URL."""

    require_signed_urls: bool = False
    metadata: Optional[dict[str, str]] = None


class DirectUploadResponse(BaseModel):
    """Cloudflare Images direct upload credentials."""

    upload_url: str = Field(..., description="One-time Cloudflare direct upload URL")
    image_id: str = Field(..., description="Cloudflare image identifier")
    public_url: Optional[str] = Field(
        default=None,
        description="Predicted public CDN URL once the image is uploaded",
    )


class UploadResultResponse(BaseModel):
    """Result after a server-side multipart upload to Cloudflare Images."""

    image_id: str
    public_url: str
    variants: list[str] = Field(default_factory=list)
