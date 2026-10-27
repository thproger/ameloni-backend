"""Authentication and registration business logic."""

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    NGORegisterRequest,
    TokenResponse,
    UserPublic,
    UserRegisterRequest,
)


async def register_user(payload: UserRegisterRequest) -> User:
    """Register a new regular USER account."""
    existing = await User.find_one(User.email == payload.email.lower())
    if existing is not None:
        raise ConflictError("Email already registered")

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        role=UserRole.USER,
        full_name=payload.full_name.strip(),
    )
    await user.insert()
    return user


async def register_ngo(payload: NGORegisterRequest) -> User:
    """Register a new NGO organizer account."""
    existing = await User.find_one(User.email == payload.email.lower())
    if existing is not None:
        raise ConflictError("Email already registered")

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        role=UserRole.NGO,
        full_name=payload.full_name.strip(),
        organization_name=payload.organization_name.strip(),
        logo_url=payload.logo_url,
        contact_info=payload.contact_info,
        description=payload.description,
    )
    await user.insert()
    return user


async def authenticate(payload: LoginRequest) -> TokenResponse:
    """Validate credentials and return a JWT access token."""
    user = await User.find_one(User.email == payload.email.lower())
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise UnauthorizedError("Incorrect email or password")
    if not user.is_active:
        raise UnauthorizedError("User account is inactive")

    token = create_access_token(subject=str(user.id), role=user.role.value)
    return TokenResponse(access_token=token, role=user.role)


def to_user_public(user: User) -> UserPublic:
    """Map a User document to the public API schema."""
    return UserPublic(
        _id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name,
        organization_name=user.organization_name,
        logo_url=user.logo_url,
        contact_info=user.contact_info,
        description=user.description,
    )
