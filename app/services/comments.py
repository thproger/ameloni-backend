"""Comment business logic with dual-visibility rules."""

from typing import Optional

from beanie import Link, PydanticObjectId

from app.core.exceptions import NotFoundError
from app.models.comment import Comment
from app.models.event import Event
from app.models.user import User, UserRole
from app.schemas.comment import CommentCreate, CommentListResponse, CommentPublic


def _extract_ref_id(ref: object) -> PydanticObjectId:
    """Resolve a Beanie Link or raw ObjectId to PydanticObjectId."""
    if isinstance(ref, Link):
        return ref.ref.id  # type: ignore[attr-defined]
    if isinstance(ref, PydanticObjectId):
        return ref
    if hasattr(ref, "id"):
        return ref.id  # type: ignore[return-value]
    return PydanticObjectId(str(ref))


def _is_event_owner(event: Event, user: Optional[User]) -> bool:
    if user is None or user.role != UserRole.NGO:
        return False
    return _extract_ref_id(event.organization_id) == user.id


async def create_comment(
    event_id: PydanticObjectId,
    payload: CommentCreate,
    author: User,
) -> CommentPublic:
    """Add a comment to an event.

    Organizer-only comments may only be created by authenticated users;
    visibility is enforced on read. Any authenticated user may post either type.
    """
    event = await Event.get(event_id)
    if event is None:
        raise NotFoundError("Event not found")

    # Only the organizing NGO (or we allow any auth user) — keep open for USER+NGO
    # Organizer-only flag is a visibility flag, not a permission gate on create.
    comment = Comment(
        event_id=event,  # type: ignore[arg-type]
        author_id=author,  # type: ignore[arg-type]
        text=payload.text.strip(),
        is_organizer_only=payload.is_organizer_only,
    )
    await comment.insert()
    return await to_comment_public(comment, author_name=author.full_name)


async def list_comments(
    event_id: PydanticObjectId,
    viewer: Optional[User],
) -> CommentListResponse:
    """Return comments visible to the viewer.

    - Unauthenticated / regular USER: public comments only.
    - NGO owner of the event: all comments (public + organizer-only).
    """
    event = await Event.get(event_id)
    if event is None:
        raise NotFoundError("Event not found")

    query = Comment.find(Comment.event_id.id == event_id)  # type: ignore[attr-defined]
    if not _is_event_owner(event, viewer):
        query = query.find(Comment.is_organizer_only == False)  # noqa: E712

    comments = await query.sort(+Comment.created_at).to_list()
    items: list[CommentPublic] = []
    for comment in comments:
        author_name: Optional[str] = None
        try:
            author = await comment.author_id.fetch()  # type: ignore[union-attr]
            if isinstance(author, User):
                author_name = author.full_name
        except Exception:
            author_name = None
        items.append(await to_comment_public(comment, author_name=author_name))

    return CommentListResponse(items=items, total=len(items))


async def to_comment_public(
    comment: Comment,
    *,
    author_name: Optional[str] = None,
) -> CommentPublic:
    """Map a Comment document to the public schema."""
    return CommentPublic(
        id=comment.id,  # type: ignore[arg-type]
        event_id=_extract_ref_id(comment.event_id),
        author_id=_extract_ref_id(comment.author_id),
        author_name=author_name,
        text=comment.text,
        is_organizer_only=comment.is_organizer_only,
        created_at=comment.created_at,
    )


# Re-export helper for events service
is_event_owner = _is_event_owner
extract_ref_id = _extract_ref_id
