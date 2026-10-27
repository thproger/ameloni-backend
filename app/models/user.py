"""User document model (regular users and NGO organizers)."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document, Indexed
from pydantic import EmailStr, Field
from pymongo import IndexModel


class UserRole(str, Enum):
    """Application user roles."""

    USER = "USER"
    NGO = "NGO"


class User(Document):
    """Registered user — either a regular USER or an NGO organizer."""

    email: Indexed(EmailStr, unique=True)  # type: ignore[valid-type]
    hashed_password: str
    role: UserRole
    full_name: str = Field(..., min_length=1, max_length=200)

    # NGO-specific fields (optional for USER role)
    organization_name: Optional[str] = Field(default=None, max_length=300)
    logo_url: Optional[str] = None
    contact_info: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None, max_length=2000)

    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("role", 1)]),
            IndexModel([("organization_name", 1)]),
        ]

    def touch(self) -> None:
        """Update the `updated_at` timestamp."""
        self.updated_at = datetime.now(timezone.utc)
