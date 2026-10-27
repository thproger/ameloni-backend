"""Aggregate API v1 routers under a single router."""

from fastapi import APIRouter

from app.api.v1 import auth, events, media, openapi_routes
from app.core.config import get_settings


def build_api_router() -> APIRouter:
    """Create the versioned API router with all v1 endpoints."""
    settings = get_settings()
    router = APIRouter(prefix=settings.api_v1_prefix)
    router.include_router(auth.router)
    router.include_router(events.router)
    router.include_router(media.router)
    router.include_router(openapi_routes.router)
    return router


api_router = build_api_router()
