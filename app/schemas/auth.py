"""Authentication request/response schemas."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole
from app.schemas.common import ORMModel, PyObjectId


class UserRegisterRequest(BaseModel):
    """Registration payload for a regular USER."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=200)


class NGORegisterRequest(BaseModel):
    """Registration payload for an NGO organizer."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=200)
    organization_name: str = Field(..., min_length=1, max_length=300)
    logo_url: Optional[str] = None
    contact_info: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None, max_length=2000)


class LoginRequest(BaseModel):
    """Login credentials."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"
    role: UserRole


class UserPublic(ORMModel):
    """Public user profile returned by `/auth/me` and nested in responses."""

    id: PyObjectId = Field(..., alias="_id", serialization_alias="id")
    email: EmailStr
    role: UserRole
    full_name: str
    organization_name: Optional[str] = None
    logo_url: Optional[str] = None
    contact_info: Optional[str] = None
    description: Optional[str] = None

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, value: object) -> object:
        return value
