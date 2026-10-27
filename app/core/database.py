"""MongoDB / Beanie lifecycle helpers."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie

from app.core.config import get_settings

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    """Return the shared Motor client (must be initialized first)."""
    if _client is None:
        raise RuntimeError("MongoDB client is not initialized. Call connect_to_mongo() first.")
    return _client


def get_database() -> AsyncIOMotorDatabase:
    """Return the configured application database."""
    settings = get_settings()
    return get_client()[settings.mongodb_db_name]


async def connect_to_mongo() -> None:
    """Open the Motor client and initialize Beanie document models."""
    global _client
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_uri)

    # Import here to avoid circular imports at module load time
    from app.models.user import User
    from app.models.event import Event
    from app.models.comment import Comment

    await init_beanie(
        database=get_database(),
        document_models=[User, Event, Comment],
    )


async def close_mongo_connection() -> None:
    """Close the Motor client gracefully."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
