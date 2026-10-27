"""Comment document model with dual visibility (public / organizer-only)."""

from datetime import datetime, timezone

from beanie import Document, Link
from pydantic import Field
from pymongo import IndexModel, ASCENDING

from app.models.event import Event
from app.models.user import User


class Comment(Document):
    """Event comment — public or visible only to the organizing NGO."""

    event_id: Link[Event]
    author_id: Link[User]
    text: str = Field(..., min_length=1, max_length=5000)
    is_organizer_only: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "comments"
        indexes = [
            IndexModel([("event_id", ASCENDING), ("created_at", ASCENDING)]),
            IndexModel([("event_id", ASCENDING), ("is_organizer_only", ASCENDING)]),
            IndexModel([("author_id", ASCENDING)]),
        ]
