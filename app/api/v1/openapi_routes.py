"""Custom OpenAPI document endpoints for codegen tools."""

from typing import Any

import yaml
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

router = APIRouter(tags=["OpenAPI"])


@router.get(
    "/openapi.json",
    summary="OpenAPI 3 schema (JSON)",
    include_in_schema=False,
)
async def openapi_json(request: Request) -> JSONResponse:
    """Serve the generated OpenAPI schema as JSON (for Orval / openapi-generator)."""
    schema: dict[str, Any] = request.app.openapi()
    return JSONResponse(content=schema)


@router.get(
    "/openapi.yaml",
    summary="OpenAPI 3 schema (YAML)",
    include_in_schema=False,
)
async def openapi_yaml(request: Request) -> Response:
    """Serve the generated OpenAPI schema as YAML."""
    schema: dict[str, Any] = request.app.openapi()
    body = yaml.safe_dump(schema, sort_keys=False, allow_unicode=True)
    return Response(content=body, media_type="application/yaml")
