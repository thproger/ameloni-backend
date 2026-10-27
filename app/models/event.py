"""Event document model."""

from datetime import datetime, timezone
from typing import List, Optional

from beanie import Document, Link, PydanticObjectId
from pydantic import Field
from pymongo import IndexModel, ASCENDING, TEXT

from app.models.user import User


class Event(Document):
    """Public event listing posted by an NGO organizer."""

    title: str = Field(..., min_length=1, max_length=300)
    description_markdown: str = Field(..., min_length=1)
    poster_url: Optional[str] = None

    organization_id: Link[User]
    organization_name: str = Field(..., min_length=1, max_length=300)

    start_date_time: datetime
    end_date_time: Optional[datetime] = None
    is_multiday: bool = False
    days_of_week: List[str] = Field(default_factory=list)

    location: str = Field(..., min_length=1, max_length=500)
    is_reimbursable: bool = False
    tags: List[str] = Field(default_factory=list)

    likes_count: int = Field(default=0, ge=0)
    liked_by_user_ids: List[PydanticObjectId] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "events"
        indexes = [
            IndexModel([("title", TEXT), ("description_markdown", TEXT)], name="event_text"),
            IndexModel([("tags", ASCENDING)]),
            IndexModel([("location", ASCENDING)]),
            IndexModel([("start_date_time", ASCENDING)]),
            IndexModel([("is_multiday", ASCENDING)]),
            IndexModel([("is_reimbursable", ASCENDING)]),
            IndexModel([("days_of_week", ASCENDING)]),
            IndexModel([("organization_id", ASCENDING)]),
            IndexModel([("created_at", ASCENDING)]),
        ]

    def touch(self) -> None:
        """Update the `updated_at` timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def is_liked_by(self, user_id: PydanticObjectId | None) -> bool:
        """Return whether the given user has liked this event."""
        if user_id is None:
            return False
        return user_id in self.liked_by_user_ids
