"""The OpenAPI document is a contract, so it is asserted like one."""

from __future__ import annotations

from typing import Any

from ai_workspace_api.api.app import create_app
from ai_workspace_api.api.openapi import assert_unique_operation_ids
from ai_workspace_api.core.settings import Settings

from .conftest import BuildSettings, running_app


def schema_of(settings: Settings) -> dict[str, Any]:
    document: dict[str, Any] = create_app(settings).openapi()
    return document


def test_operation_ids_are_readable_and_do_not_encode_the_path(settings: Settings) -> None:
    """FastAPI's default id embeds the path, so moving a route renames a
    generated client's method."""
    schema = schema_of(settings)
    ids = [
        operation["operationId"]
        for path in schema["paths"].values()
        for operation in path.values()
        if "operationId" in operation
    ]

    assert ids
    assert all("api_v1" not in name and "__" not in name for name in ids), ids
    assert "live" in ids and "ready" in ids


def test_duplicate_operation_ids_are_refused() -> None:
    """Two operations sharing an id produce a client missing one of them."""
    schema = {
        "paths": {
            "/one": {"get": {"operationId": "clash"}},
            "/two": {"get": {"operationId": "clash"}},
        }
    }

    try:
        assert_unique_operation_ids(schema)
    except ValueError as error:
        assert "clash" in str(error)
    else:  # pragma: no cover - the assertion above is the point
        raise AssertionError("a duplicate operation id was accepted")


def test_every_operation_documents_the_error_envelope(settings: Settings) -> None:
    """A client written against a schema that lists only 200 does not know the
    envelope exists."""
    schema = schema_of(settings)

    for path, operations in schema["paths"].items():
        for method, operation in operations.items():
            assert "422" in operation["responses"], f"{method} {path}"
            assert "500" in operation["responses"], f"{method} {path}"


def test_the_error_envelope_is_in_the_schema(settings: Settings) -> None:
    schema = schema_of(settings)
    envelope = schema["components"]["schemas"]["ErrorResponse"]

    assert set(envelope["properties"]) >= {"code", "message", "detail", "request_id"}


def test_the_description_explains_the_error_contract(settings: Settings) -> None:
    description = schema_of(settings)["info"]["description"]

    assert "X-Request-ID" in description
    assert "code" in description


def test_health_operations_are_tagged(settings: Settings) -> None:
    schema = schema_of(settings)

    assert schema["paths"]["/health/live"]["get"]["tags"] == ["health"]
    assert {tag["name"] for tag in schema["tags"]} >= {"health", "meta"}


async def test_docs_are_served_locally_and_closed_elsewhere(
    valid_env: dict[str, str], settings_from: BuildSettings
) -> None:
    local = create_app(settings_from({**valid_env, "ENVIRONMENT": "local"}))
    production = create_app(settings_from({**valid_env, "ENVIRONMENT": "production"}))

    async with running_app(local) as client:
        assert (await client.get("/docs")).status_code == 200
        assert (await client.get("/openapi.json")).status_code == 200

    async with running_app(production) as client:
        assert (await client.get("/docs")).status_code == 404
        assert (await client.get("/openapi.json")).status_code == 404


def test_the_schema_is_built_once(settings: Settings) -> None:
    """It is rebuilt on every request otherwise, which is slow and pointless."""
    app = create_app(settings)

    assert app.openapi() is app.openapi()
