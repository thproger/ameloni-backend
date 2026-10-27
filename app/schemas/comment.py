"""Comment request/response schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel, PyObjectId


class CommentCreate(BaseModel):
    """Payload for posting a comment on an event."""

    text: str = Field(..., min_length=1, max_length=5000)
    is_organizer_only: bool = False


class CommentPublic(ORMModel):
    """Comment as returned to clients (visibility already filtered)."""

    id: PyObjectId
    event_id: PyObjectId
    author_id: PyObjectId
    author_name: Optional[str] = None
    text: str
    is_organizer_only: bool = False
    created_at: datetime


class CommentListResponse(BaseModel):
    """List of comments for an event."""

    items: List[CommentPublic]
    total: int = Field(..., ge=0)
