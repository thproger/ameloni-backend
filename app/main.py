"""FastAPI application factory and ASGI entrypoint."""

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app import __version__
from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import close_mongo_connection, connect_to_mongo


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown hooks: MongoDB + Beanie."""
    await connect_to_mongo()
    yield
    await close_mongo_connection()


def custom_openapi(app: FastAPI) -> dict[str, Any]:
    """Build a custom OpenAPI 3 schema with JWT Bearer security and rich tags."""
    if app.openapi_schema:
        return app.openapi_schema

    settings = get_settings()
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=__version__,
        description=(
            "REST API for **Афіша подій** — an Event Poster / Recommendation platform.\n\n"
            "### Roles\n"
            "- **Anonymous** — read public events, details, and public comments.\n"
            "- **USER** — like events, post comments.\n"
            "- **NGO** — create/update/delete own events, view organizer-only comments, upload media.\n\n"
            "### Auth\n"
            "Obtain a JWT via `POST /api/v1/auth/login`, then send "
            "`Authorization: Bearer <token>` on protected routes."
        ),
        routes=app.routes,
        tags=[
            {
                "name": "Authentication",
                "description": "Registration, login, and current-user profile",
            },
            {
                "name": "Events",
                "description": "Event listing, filtering, CRUD, and likes",
            },
            {
                "name": "Comments",
                "description": "Public and organizer-only comments",
            },
            {
                "name": "Media",
                "description": "Cloudflare Images direct upload & multipart upload",
            },
            {
                "name": "Health",
                "description": "Liveness / readiness probes",
            },
        ],
    )

    components = openapi_schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["HTTPBearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Paste the JWT access token obtained from `/auth/login`.",
    }

    # Apply Bearer security globally; public routes override with security: []
    openapi_schema["security"] = [{"HTTPBearer": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/health", tags=["Health"], summary="Liveness probe")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.openapi = lambda: custom_openapi(app)  # type: ignore[method-assign]
    return app


app = create_app()
