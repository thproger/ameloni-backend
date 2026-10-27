"""Shared schema primitives."""

from typing import Generic, List, TypeVar

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PyObjectId(PydanticObjectId):
    """Alias for Beanie's PydanticObjectId used in API schemas."""

    pass


class ORMModel(BaseModel):
    """Base schema that allows reading from ORM / Beanie documents."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MessageResponse(BaseModel):
    """Simple message payload."""

    message: str


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated list wrapper."""

    items: List[T]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1)
    pages: int = Field(..., ge=0)
