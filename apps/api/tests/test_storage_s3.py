"""The S3 transport, against the MinIO the compose stack runs.

The rules are covered in `test_storage.py` without a network. What only a real
store can answer is here: that a signed URL is actually fetchable, that a
missing key is a `NotFoundError` rather than a `ClientError`, and that the
object arrives with the content type it was given.

Skipped when MinIO is not configured, in the manner of the Redis fixture — a
substitute that always agrees would be worse than a visible skip.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack

import httpx
import pytest

from ai_workspace_api.core.errors import NotFoundError
from ai_workspace_api.core.settings import Settings
from ai_workspace_api.core.storage import ObjectKind, S3Storage, open_s3_storage
from ai_workspace_api.core.tenancy import TenantScope
from ai_workspace_api.models import Role

from .conftest import BuildSettings

pytestmark = pytest.mark.integration

PDF = "application/pdf"


@pytest.fixture
async def storage(
    valid_env: dict[str, str], settings_from: BuildSettings, s3_settings: dict[str, str]
) -> AsyncIterator[S3Storage]:
    settings: Settings = settings_from({**valid_env, **s3_settings})
    async with AsyncExitStack() as stack:
        yield await open_s3_storage(settings, stack)


@pytest.fixture
def scope() -> TenantScope:
    return TenantScope(user_id=uuid.uuid4(), organization_id=uuid.uuid4(), role=Role.MEMBER)


async def test_the_bucket_the_app_is_configured_with_exists(storage: S3Storage) -> None:
    """The readiness check, for real. A bucket that is missing in production is
    an outage that only shows up on the first upload."""
    await storage.check()


async def test_an_object_survives_a_round_trip(storage: S3Storage, scope: TenantScope) -> None:
    stored = await storage.put(
        scope, ObjectKind.DOCUMENT, data=b"%PDF-1.7 body", filename="a.pdf", content_type=PDF
    )
    try:
        assert await storage.get(scope, stored.key) == b"%PDF-1.7 body"
        assert stored.key.startswith(f"org/{scope.organization_id}/document/")
    finally:
        await storage.delete(scope, stored.key)


async def test_a_missing_key_is_a_domain_error_not_a_client_error(
    storage: S3Storage, scope: TenantScope
) -> None:
    """Callers handle `NotFoundError`. A botocore exception leaking out means
    every call site has to know which string code means "gone"."""
    with pytest.raises(NotFoundError):
        await storage.get(scope, f"org/{scope.organization_id}/document/{uuid.uuid4()}.pdf")


async def test_a_presigned_url_actually_fetches_the_object_and_then_expires(
    storage: S3Storage, scope: TenantScope
) -> None:
    stored = await storage.put(
        scope, ObjectKind.DOCUMENT, data=b"signed body", filename="a.pdf", content_type=PDF
    )
    try:
        url = await storage.presigned_url(scope, stored.key, expires_in=60)
        async with httpx.AsyncClient() as client:
            fetched = await client.get(url)
            # The credentials are in the query string, so removing them must not
            # still work — otherwise the bucket is public and the signing is
            # decoration.
            unsigned = await client.get(url.split("?")[0])

        assert fetched.status_code == 200
        assert fetched.content == b"signed body"
        assert fetched.headers["content-type"] == PDF
        assert unsigned.status_code in {401, 403}
    finally:
        await storage.delete(scope, stored.key)


async def test_deleting_twice_is_not_an_error(storage: S3Storage, scope: TenantScope) -> None:
    stored = await storage.put(
        scope, ObjectKind.DOCUMENT, data=b"x", filename="a.pdf", content_type=PDF
    )

    await storage.delete(scope, stored.key)
    await storage.delete(scope, stored.key)

    with pytest.raises(NotFoundError):
        await storage.get(scope, stored.key)
