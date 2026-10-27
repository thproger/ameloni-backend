"""Authentication endpoints: register, login, me."""

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser
from app.schemas.auth import (
    LoginRequest,
    NGORegisterRequest,
    TokenResponse,
    UserPublic,
    UserRegisterRequest,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register/user",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register a regular user",
)
async def register_user(payload: UserRegisterRequest) -> UserPublic:
    """Create a USER account that can view events, like, and comment publicly."""
    user = await auth_service.register_user(payload)
    return auth_service.to_user_public(user)


@router.post(
    "/register/ngo",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register an NGO organizer",
)
async def register_ngo(payload: NGORegisterRequest) -> UserPublic:
    """Create an NGO account that can CRUD own events and see organizer-only comments."""
    user = await auth_service.register_ngo(payload)
    return auth_service.to_user_public(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and obtain JWT access token",
)
async def login(payload: LoginRequest) -> TokenResponse:
    """Authenticate with email/password and receive a Bearer JWT."""
    return await auth_service.authenticate(payload)


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get current authenticated user profile",
)
async def get_me(current_user: CurrentUser) -> UserPublic:
    """Return the profile of the user identified by the Bearer token."""
    return auth_service.to_user_public(current_user)
