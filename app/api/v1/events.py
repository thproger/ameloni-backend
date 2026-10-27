"""Event listing, CRUD, likes, and comments endpoints."""

from datetime import datetime
from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentNGO, CurrentUser, OptionalUser
from app.schemas.comment import CommentCreate, CommentListResponse, CommentPublic
from app.schemas.common import MessageResponse
from app.schemas.event import (
    EventCreate,
    EventDetail,
    EventListResponse,
    EventUpdate,
    LikeToggleResponse,
)
from app.services import comments as comments_service
from app.services import events as events_service

router = APIRouter(prefix="/events", tags=["Events"])


@router.get(
    "",
    response_model=EventListResponse,
    summary="List / filter events (public)",
)
async def list_events(
    current_user: OptionalUser,
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Text search in title/description"),
    tags: Optional[List[str]] = Query(None, description="Filter by hashtags"),
    location: Optional[str] = Query(None, description="City / address substring"),
    is_multiday: Optional[bool] = Query(None),
    days_of_week: Optional[List[str]] = Query(
        None,
        description="Filter by weekdays, e.g. Monday,Thursday",
    ),
    is_reimbursable: Optional[bool] = Query(None),
    start_date_from: Optional[datetime] = Query(
        None, description="Inclusive lower bound for start_date_time"
    ),
    start_date_to: Optional[datetime] = Query(
        None, description="Inclusive upper bound for start_date_time"
    ),
) -> EventListResponse:
    """Return paginated event cards optimised for the feed UI.

    Anonymous callers receive `is_liked=false` for all items.
    Authenticated callers get personalised like state.
    """
    return await events_service.list_events(
        page=page,
        limit=limit,
        search=search,
        tags=tags,
        location=location,
        is_multiday=is_multiday,
        days_of_week=days_of_week,
        is_reimbursable=is_reimbursable,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        viewer=current_user,
    )


@router.get(
    "/{event_id}",
    response_model=EventDetail,
    summary="Get event details (public)",
)
async def get_event(
    event_id: PydanticObjectId,
    current_user: OptionalUser,
) -> EventDetail:
    """Full event payload including markdown body, organizer, and visible comments."""
    return await events_service.get_event_detail(event_id, viewer=current_user)


@router.post(
    "",
    response_model=EventDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create event (NGO only)",
)
async def create_event(
    payload: EventCreate,
    current_user: CurrentNGO,
) -> EventDetail:
    """Create a new event owned by the authenticated NGO organizer."""
    return await events_service.create_event(payload, organizer=current_user)


@router.put(
    "/{event_id}",
    response_model=EventDetail,
    summary="Update owned event (NGO only)",
)
async def update_event(
    event_id: PydanticObjectId,
    payload: EventUpdate,
    current_user: CurrentNGO,
) -> EventDetail:
    """Update an event; only the owning NGO may modify it."""
    return await events_service.update_event(event_id, payload, organizer=current_user)


@router.delete(
    "/{event_id}",
    response_model=MessageResponse,
    summary="Delete owned event (NGO only)",
)
async def delete_event(
    event_id: PydanticObjectId,
    current_user: CurrentNGO,
) -> MessageResponse:
    """Delete an owned event and cascade-delete its comments."""
    await events_service.delete_event(event_id, organizer=current_user)
    return MessageResponse(message="Event deleted")


@router.post(
    "/{event_id}/like",
    response_model=LikeToggleResponse,
    summary="Toggle like on an event",
)
async def toggle_like(
    event_id: PydanticObjectId,
    current_user: CurrentUser,
) -> LikeToggleResponse:
    """Toggle the current user's like on the given event."""
    return await events_service.toggle_like(event_id, user=current_user)


@router.post(
    "/{event_id}/comments",
    response_model=CommentPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment",
    tags=["Comments"],
)
async def add_comment(
    event_id: PydanticObjectId,
    payload: CommentCreate,
    current_user: CurrentUser,
) -> CommentPublic:
    """Post a public or organizer-only comment on an event."""
    return await comments_service.create_comment(event_id, payload, author=current_user)


@router.get(
    "/{event_id}/comments",
    response_model=CommentListResponse,
    summary="List comments for an event",
    tags=["Comments"],
)
async def get_comments(
    event_id: PydanticObjectId,
    current_user: OptionalUser,
) -> CommentListResponse:
    """Return comments visible to the caller.

    Public comments for everyone; organizer-only comments only for the owning NGO.
    """
    return await comments_service.list_comments(event_id, viewer=current_user)
