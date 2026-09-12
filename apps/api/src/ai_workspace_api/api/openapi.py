"""OpenAPI document shaping.

The schema is a contract, not a by-product. Two things follow from that:

- **Operation ids are stable and readable.** FastAPI derives them from the
  function name plus the path, which changes whenever a route moves — and a
  generated client renames its methods with it. Deriving from the route name
  keeps them stable across refactors.
- **Every operation documents its failures.** A client written against a schema
  that only lists 200 has no idea the error envelope exists.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

from ai_workspace_api.core.settings import Settings
from ai_workspace_api.schemas.errors import ErrorResponse

DESCRIPTION = """\
Multi-tenant document intelligence. Upload documents, search them semantically,
and ask questions that come back with citations.

**Errors.** Every failure uses one envelope: a stable machine-readable `code`, a
`message` safe to show a user, an optional `detail` array of field errors for a
422, and a `request_id` matching the `X-Request-ID` response header — quote it in
a bug report.
"""

# Applied to every operation. Individual routes add their own on top.
COMMON_RESPONSES: dict[int | str, dict[str, Any]] = {
    422: {"model": ErrorResponse, "description": "The request failed validation"},
    500: {"model": ErrorResponse, "description": "Unexpected server error"},
}


def route_name_operation_id(route: APIRoute) -> str:
    """The operation id a generated client turns into a method name.

    FastAPI's default embeds the path — `list_documents_api_v1_documents_get` —
    so moving a route renames the client's method. Passed to FastAPI as
    `generate_unique_id_function` rather than applied by walking `app.routes`,
    which does not contain the routes of included routers in FastAPI 0.141.
    """
    return route.name


def assert_unique_operation_ids(schema: dict[str, Any]) -> None:
    """Two operations sharing an id produce a client silently missing one.

    Checked on the built document because that is the only place every route is
    visible once routers are included.
    """
    seen: set[str] = set()
    for path, operations in schema.get("paths", {}).items():
        for method, operation in operations.items():
            name = operation.get("operationId")
            if name is None:
                continue
            if name in seen:
                raise ValueError(f"duplicate operation id {name!r} at {method.upper()} {path}")
            seen.add(name)


def custom_openapi(app: FastAPI, settings: Settings) -> Any:
    """Builds the document once and caches it on the app, as FastAPI does."""

    def build() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=DESCRIPTION,
            routes=app.routes,
            tags=TAGS,
            servers=[{"url": "/", "description": settings.environment.value}],
        )
        schema["info"]["contact"] = {"name": "AI Workspace"}
        assert_unique_operation_ids(schema)
        app.openapi_schema = schema
        return schema

    return build


TAGS = [
    {"name": "health", "description": "Liveness and readiness probes. Not versioned."},
    {"name": "meta", "description": "Service identity."},
]
