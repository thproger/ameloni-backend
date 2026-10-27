"""FastAPI dependency injection helpers (auth, current user)."""

from typing import Annotated, Optional

from beanie import PydanticObjectId
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(bearer_scheme),
    ],
) -> Optional[User]:
    """Resolve the current user if a valid Bearer token is present; else None."""
    if credentials is None or not credentials.credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = await User.get(PydanticObjectId(user_id))
        if user is None or not user.is_active:
            return None
        return user
    except (JWTError, ValueError):
        return None


async def get_current_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(bearer_scheme),
    ],
) -> User:
    """Require a valid authenticated user."""
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError()
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError()
        user = await User.get(PydanticObjectId(user_id))
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or inactive")
        return user
    except (JWTError, ValueError) as exc:
        raise UnauthorizedError() from exc


async def get_current_ngo(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require an authenticated NGO organizer."""
    if current_user.role != UserRole.NGO:
        raise ForbiddenError("NGO organizer role required")
    return current_user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentNGO = Annotated[User, Depends(get_current_ngo)]
OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]
