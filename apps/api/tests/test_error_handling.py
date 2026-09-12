"""Every failure comes back in one envelope, and none of them leaks internals."""

from __future__ import annotations

import pytest
from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

from ai_workspace_api.api.app import create_app
from ai_workspace_api.core.errors import (
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from ai_workspace_api.core.settings import Settings

from .conftest import running_app

SECRET_IN_MESSAGE = "postgresql://admin:hunter2@db.internal:5432/prod"


class Payload(BaseModel):
    name: str
    count: int


def app_with_failing_routes(settings: Settings) -> FastAPI:
    """Routes that fail in each way a real handler can."""
    app = create_app(settings)
    router = APIRouter()

    @router.get("/boom/not-found")
    async def not_found() -> None:
        raise NotFoundError("That document does not exist.")

    @router.get("/boom/forbidden")
    async def forbidden() -> None:
        raise PermissionDeniedError("You cannot change another member's role.")

    @router.get("/boom/conflict")
    async def conflict() -> None:
        raise ConflictError("That address is already in use.")

    @router.get("/boom/validation")
    async def validation() -> None:
        raise ValidationError(
            "The workspace could not be created.",
            detail=[{"field": "slug", "message": "This address is already in use."}],
        )

    @router.get("/boom/unexpected")
    async def unexpected() -> None:
        raise RuntimeError(f"connection failed: {SECRET_IN_MESSAGE}")

    @router.post("/boom/body")
    async def body(payload: Payload) -> Payload:
        return payload

    app.include_router(router)
    return app


@pytest.mark.parametrize(
    ("path", "status", "code"),
    [
        ("/boom/not-found", 404, "not_found"),
        ("/boom/forbidden", 403, "permission_denied"),
        ("/boom/conflict", 409, "conflict"),
        ("/boom/validation", 422, "validation_failed"),
    ],
)
async def test_domain_errors_map_to_their_status_and_code(
    settings: Settings, path: str, status: int, code: str
) -> None:
    async with running_app(app_with_failing_routes(settings)) as client:
        response = await client.get(path)

    assert response.status_code == status
    body = response.json()
    assert body["code"] == code
    assert body["message"]
    assert body["request_id"], "the reference must be present to be quotable"


async def test_a_validation_error_carries_field_detail(settings: Settings) -> None:
    """The web form layer maps these back onto their fields."""
    async with running_app(app_with_failing_routes(settings)) as client:
        body = (await client.get("/boom/validation")).json()

    assert body["detail"] == [{"field": "slug", "message": "This address is already in use."}]


async def test_an_unexpected_error_leaks_nothing(settings: Settings) -> None:
    """The one that matters. A driver message contains hosts and credentials."""
    async with running_app(app_with_failing_routes(settings), raise_app_exceptions=False) as client:
        response = await client.get("/boom/unexpected")

    assert response.status_code == 500
    raw = response.text
    assert "hunter2" not in raw
    assert "db.internal" not in raw
    assert "RuntimeError" not in raw
    assert "Traceback" not in raw
    body = response.json()
    assert body["code"] == "internal_error"
    assert body["request_id"]


async def test_the_reference_matches_the_response_header(settings: Settings) -> None:
    """Otherwise the id a user quotes finds nothing in the logs."""
    async with running_app(app_with_failing_routes(settings), raise_app_exceptions=False) as client:
        response = await client.get("/boom/unexpected")

    assert response.json()["request_id"] == response.headers["X-Request-ID"]


async def test_request_body_validation_uses_the_same_envelope(settings: Settings) -> None:
    """FastAPI's own 422 would otherwise have a different shape from ours."""
    async with running_app(app_with_failing_routes(settings)) as client:
        response = await client.post("/boom/body", json={"count": "not a number"})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_failed"
    fields = {item["field"] for item in body["detail"]}
    assert fields == {"name", "count"}, body["detail"]


async def test_an_unmatched_route_uses_the_same_envelope(settings: Settings) -> None:
    async with running_app(create_app(settings)) as client:
        response = await client.get("/nothing-here")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


async def test_a_wrong_method_uses_the_same_envelope(settings: Settings) -> None:
    async with running_app(create_app(settings)) as client:
        response = await client.post("/health/live")

    assert response.status_code == 405
    assert response.json()["code"] == "method_not_allowed"


def test_every_domain_error_declares_a_code_and_status() -> None:
    """A subclass that forgets either inherits 500/internal_error silently."""
    for subclass in DomainError.__subclasses__():
        assert subclass.code != DomainError.code, f"{subclass.__name__} has no code"
        assert 400 <= subclass.status_code < 600, subclass.__name__
