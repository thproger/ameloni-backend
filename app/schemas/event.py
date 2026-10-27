"""Event request/response schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.common import ORMModel, PaginatedResponse, PyObjectId
from app.schemas.comment import CommentPublic
from app.schemas.auth import UserPublic


ALLOWED_DAYS = {
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
}


class EventCreate(BaseModel):
    """Payload for creating an event (NGO questionnaire / form)."""

    title: str = Field(..., min_length=1, max_length=300)
    description_markdown: str = Field(..., min_length=1)
    poster_url: Optional[str] = None
    start_date_time: datetime
    end_date_time: Optional[datetime] = None
    is_multiday: bool = False
    days_of_week: List[str] = Field(default_factory=list)
    location: str = Field(..., min_length=1, max_length=500)
    is_reimbursable: bool = False
    tags: List[str] = Field(default_factory=list)

    @field_validator("days_of_week")
    @classmethod
    def validate_days(cls, value: List[str]) -> List[str]:
        normalized: list[str] = []
        for day in value:
            cleaned = day.strip().capitalize() if day else day
            if cleaned not in ALLOWED_DAYS:
                raise ValueError(
                    f"Invalid day '{day}'. Allowed: {', '.join(sorted(ALLOWED_DAYS))}"
                )
            if cleaned not in normalized:
                normalized.append(cleaned)
        return normalized

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: List[str]) -> List[str]:
        tags: list[str] = []
        for tag in value:
            cleaned = tag.strip()
            if not cleaned:
                continue
            if not cleaned.startswith("#"):
                cleaned = f"#{cleaned}"
            if cleaned not in tags:
                tags.append(cleaned)
        return tags

    @model_validator(mode="after")
    def validate_dates(self) -> "EventCreate":
        if self.end_date_time and self.end_date_time < self.start_date_time:
            raise ValueError("end_date_time must be greater than or equal to start_date_time")
        return self


class EventUpdate(BaseModel):
    """Partial update payload for an owned event."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    description_markdown: Optional[str] = Field(default=None, min_length=1)
    poster_url: Optional[str] = None
    start_date_time: Optional[datetime] = None
    end_date_time: Optional[datetime] = None
    is_multiday: Optional[bool] = None
    days_of_week: Optional[List[str]] = None
    location: Optional[str] = Field(default=None, min_length=1, max_length=500)
    is_reimbursable: Optional[bool] = None
    tags: Optional[List[str]] = None

    @field_validator("days_of_week")
    @classmethod
    def validate_days(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return value
        return EventCreate.validate_days(value)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return value
        return EventCreate.normalize_tags(value)


class EventCard(ORMModel):
    """Optimised card payload for event list / feed UI."""

    id: PyObjectId
    title: str
    poster_url: Optional[str] = None
    organization_name: str
    start_date_time: datetime
    location: str
    tags: List[str] = Field(default_factory=list)
    likes_count: int = 0
    is_liked: bool = False
    is_reimbursable: bool = False
    is_multiday: bool = False


class EventDetail(ORMModel):
    """Full event details including markdown body and comments."""

    id: PyObjectId
    title: str
    description_markdown: str
    poster_url: Optional[str] = None
    organization_id: PyObjectId
    organization_name: str
    organizer: Optional[UserPublic] = None
    start_date_time: datetime
    end_date_time: Optional[datetime] = None
    is_multiday: bool = False
    days_of_week: List[str] = Field(default_factory=list)
    location: str
    is_reimbursable: bool = False
    tags: List[str] = Field(default_factory=list)
    likes_count: int = 0
    is_liked: bool = False
    created_at: datetime
    updated_at: datetime
    comments: List[CommentPublic] = Field(default_factory=list)


class EventListResponse(PaginatedResponse[EventCard]):
    """Paginated list of event cards."""

    pass


class LikeToggleResponse(BaseModel):
    """Result of toggling a like on an event."""

    event_id: PyObjectId
    liked: bool
    likes_count: int
