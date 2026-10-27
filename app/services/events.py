"""Event CRUD, filtering, likes, and card/detail serialization."""

from datetime import datetime
from math import ceil
from typing import Any, List, Optional

from beanie import PydanticObjectId
from beanie.operators import And, In, Or, RegEx

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.event import Event
from app.models.user import User, UserRole
from app.schemas.auth import UserPublic
from app.schemas.event import (
    EventCard,
    EventCreate,
    EventDetail,
    EventListResponse,
    EventUpdate,
    LikeToggleResponse,
)
from app.services.auth import to_user_public
from app.services.comments import extract_ref_id, is_event_owner, list_comments


async def create_event(payload: EventCreate, organizer: User) -> EventDetail:
    """Create a new event owned by the authenticated NGO."""
    if organizer.role != UserRole.NGO:
        raise ForbiddenError("Only NGO organizers can create events")
    if not organizer.organization_name:
        raise ForbiddenError("NGO profile is missing organization_name")

    event = Event(
        title=payload.title.strip(),
        description_markdown=payload.description_markdown,
        poster_url=payload.poster_url,
        organization_id=organizer,  # type: ignore[arg-type]
        organization_name=organizer.organization_name,
        start_date_time=payload.start_date_time,
        end_date_time=payload.end_date_time,
        is_multiday=payload.is_multiday,
        days_of_week=payload.days_of_week,
        location=payload.location.strip(),
        is_reimbursable=payload.is_reimbursable,
        tags=payload.tags,
    )
    await event.insert()
    return await to_event_detail(event, viewer=organizer)


async def update_event(
    event_id: PydanticObjectId,
    payload: EventUpdate,
    organizer: User,
) -> EventDetail:
    """Update an event owned by the authenticated NGO."""
    event = await _get_owned_event(event_id, organizer)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(event, field, value)
    event.touch()
    await event.save()
    return await to_event_detail(event, viewer=organizer)


async def delete_event(event_id: PydanticObjectId, organizer: User) -> None:
    """Delete an event owned by the authenticated NGO (and its comments)."""
    event = await _get_owned_event(event_id, organizer)
    from app.models.comment import Comment

    await Comment.find(Comment.event_id.id == event.id).delete()  # type: ignore[attr-defined]
    await event.delete()


async def get_event_detail(
    event_id: PydanticObjectId,
    viewer: Optional[User],
) -> EventDetail:
    """Return full event details including visibility-filtered comments."""
    event = await Event.get(event_id)
    if event is None:
        raise NotFoundError("Event not found")
    return await to_event_detail(event, viewer=viewer)


async def list_events(
    *,
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    tags: Optional[List[str]] = None,
    location: Optional[str] = None,
    is_multiday: Optional[bool] = None,
    days_of_week: Optional[List[str]] = None,
    is_reimbursable: Optional[bool] = None,
    start_date_from: Optional[datetime] = None,
    start_date_to: Optional[datetime] = None,
    viewer: Optional[User] = None,
) -> EventListResponse:
    """List events with pagination and multi-criteria filtering."""
    page = max(page, 1)
    limit = min(max(limit, 1), 100)

    conditions: list[Any] = []

    if search:
        term = search.strip()
        if term:
            # Case-insensitive substring match across title & description
            conditions.append(
                Or(
                    RegEx(Event.title, term, "i"),
                    RegEx(Event.description_markdown, term, "i"),
                )
            )

    if tags:
        normalized = [
            t if t.startswith("#") else f"#{t}" for t in (tag.strip() for tag in tags) if t
        ]
        if normalized:
            conditions.append(In(Event.tags, normalized))

    if location:
        conditions.append(RegEx(Event.location, location.strip(), "i"))

    if is_multiday is not None:
        conditions.append(Event.is_multiday == is_multiday)

    if days_of_week:
        normalized_days = [d.strip().capitalize() for d in days_of_week if d.strip()]
        if normalized_days:
            conditions.append(In(Event.days_of_week, normalized_days))

    if is_reimbursable is not None:
        conditions.append(Event.is_reimbursable == is_reimbursable)

    if start_date_from is not None:
        conditions.append(Event.start_date_time >= start_date_from)

    if start_date_to is not None:
        conditions.append(Event.start_date_time <= start_date_to)

    if conditions:
        query = Event.find(And(*conditions)) if len(conditions) > 1 else Event.find(conditions[0])
    else:
        query = Event.find_all()

    total = await query.count()
    events = (
        await query.sort(-Event.start_date_time)
        .skip((page - 1) * limit)
        .limit(limit)
        .to_list()
    )

    viewer_id = viewer.id if viewer else None
    cards = [to_event_card(event, viewer_id=viewer_id) for event in events]
    pages = ceil(total / limit) if total else 0

    return EventListResponse(
        items=cards,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


async def toggle_like(
    event_id: PydanticObjectId,
    user: User,
) -> LikeToggleResponse:
    """Toggle like status for the authenticated user."""
    event = await Event.get(event_id)
    if event is None:
        raise NotFoundError("Event not found")

    liked: bool
    if user.id in event.liked_by_user_ids:
        event.liked_by_user_ids = [uid for uid in event.liked_by_user_ids if uid != user.id]
        event.likes_count = max(0, event.likes_count - 1)
        liked = False
    else:
        event.liked_by_user_ids.append(user.id)  # type: ignore[arg-type]
        event.likes_count += 1
        liked = True

    event.touch()
    await event.save()
    return LikeToggleResponse(
        event_id=event.id,  # type: ignore[arg-type]
        liked=liked,
        likes_count=event.likes_count,
    )


def to_event_card(event: Event, *, viewer_id: Optional[PydanticObjectId]) -> EventCard:
    """Map an Event document to a card DTO."""
    return EventCard(
        id=event.id,  # type: ignore[arg-type]
        title=event.title,
        poster_url=event.poster_url,
        organization_name=event.organization_name,
        start_date_time=event.start_date_time,
        location=event.location,
        tags=event.tags,
        likes_count=event.likes_count,
        is_liked=event.is_liked_by(viewer_id),
        is_reimbursable=event.is_reimbursable,
        is_multiday=event.is_multiday,
    )


async def to_event_detail(event: Event, *, viewer: Optional[User]) -> EventDetail:
    """Map an Event document to a detail DTO with comments and organizer."""
    organizer: Optional[UserPublic] = None
    org_id = extract_ref_id(event.organization_id)
    try:
        org_user = await User.get(org_id)
        if org_user is not None:
            organizer = to_user_public(org_user)
    except Exception:
        organizer = None

    comments_response = await list_comments(event.id, viewer)  # type: ignore[arg-type]
    viewer_id = viewer.id if viewer else None

    return EventDetail(
        id=event.id,  # type: ignore[arg-type]
        title=event.title,
        description_markdown=event.description_markdown,
        poster_url=event.poster_url,
        organization_id=org_id,
        organization_name=event.organization_name,
        organizer=organizer,
        start_date_time=event.start_date_time,
        end_date_time=event.end_date_time,
        is_multiday=event.is_multiday,
        days_of_week=event.days_of_week,
        location=event.location,
        is_reimbursable=event.is_reimbursable,
        tags=event.tags,
        likes_count=event.likes_count,
        is_liked=event.is_liked_by(viewer_id),
        created_at=event.created_at,
        updated_at=event.updated_at,
        comments=comments_response.items,
    )


async def _get_owned_event(event_id: PydanticObjectId, organizer: User) -> Event:
    event = await Event.get(event_id)
    if event is None:
        raise NotFoundError("Event not found")
    if not is_event_owner(event, organizer):
        raise ForbiddenError("You can only modify your own events")
    return event
