"""The storage rules, exercised without a network.

`InMemoryStorage` is not a mock: it inherits the same base class, so these are
the real size, type, key and tenant rules rather than a stand-in that agrees
with them. The S3 transport is covered separately, against MinIO.
"""

from __future__ import annotations

import re
import uuid

import pytest

from ai_workspace_api.core.errors import NotFoundError, ValidationError
from ai_workspace_api.core.storage import (
    MAX_OBJECT_BYTES,
    InMemoryStorage,
    ObjectKind,
    build_key,
)
from ai_workspace_api.core.tenancy import TenantScope
from ai_workspace_api.models import Role

PDF = "application/pdf"


def scope_for(organization_id: uuid.UUID | None = None) -> TenantScope:
    return TenantScope(
        user_id=uuid.uuid4(),
        organization_id=organization_id or uuid.uuid4(),
        role=Role.MEMBER,
    )


# --- keys ---------------------------------------------------------------------


def test_a_key_names_the_organisation_the_kind_and_nothing_else() -> None:
    """Attributable from the key alone: a stray object is visible in a listing,
    not only in a join."""
    scope = scope_for()

    key = build_key(scope, ObjectKind.DOCUMENT, "Quarterly Report.pdf")

    assert re.fullmatch(rf"org/{scope.organization_id}/document/[0-9a-f-]{{36}}\.pdf", key), key


@pytest.mark.parametrize(
    "filename",
    [
        "../../../etc/passwd",
        "../../other-org/document/leak.pdf",
        "report.pdf/../../../secrets.pdf",
        "a\\b\\c.pdf",
        "report.pdf\x00.exe",
        "%2e%2e%2fsecret.pdf",
        "report .pdf ",
        "..",
        ".",
        "",
    ],
)
def test_no_filename_can_reach_outside_the_tenant_prefix(filename: str) -> None:
    """The uploaded name is never part of the key — only an extension that looks
    like one survives, so there is nothing to escape with."""
    scope = scope_for()

    key = build_key(scope, ObjectKind.DOCUMENT, filename)

    assert key.startswith(f"org/{scope.organization_id}/document/")
    assert ".." not in key
    assert key.count("/") == 3


def test_two_uploads_of_the_same_name_do_not_collide() -> None:
    scope = scope_for()

    first = build_key(scope, ObjectKind.DOCUMENT, "report.pdf")
    second = build_key(scope, ObjectKind.DOCUMENT, "report.pdf")

    assert first != second


@pytest.mark.parametrize(
    ("filename", "expected_extension"),
    [
        ("report.pdf", ".pdf"),
        ("REPORT.PDF", ".pdf"),
        ("archive.tar.gz", ".gz"),
        ("report.this-is-not-an-extension", ""),
        ("report.", ""),
        ("report", ""),
        ("report.p df", ""),
        (".gitignore", ""),
    ],
)
def test_only_something_that_looks_like_an_extension_survives(
    filename: str, expected_extension: str
) -> None:
    """The extension is the one part of a name worth keeping — it makes a bucket
    listing readable. Anything else in the name is the user's text, and text
    does not belong in a path."""
    key = build_key(scope_for(), ObjectKind.DOCUMENT, filename)
    name = key.rsplit("/", 1)[1]

    assert name == f"{uuid.UUID(name.removesuffix(expected_extension))}{expected_extension}"


# --- what may be stored -------------------------------------------------------


async def test_an_empty_file_is_refused() -> None:
    with pytest.raises(ValidationError, match="empty"):
        await InMemoryStorage().put(
            scope_for(), ObjectKind.DOCUMENT, data=b"", filename="a.pdf", content_type=PDF
        )


async def test_a_file_over_the_limit_is_refused_before_it_is_stored() -> None:
    storage = InMemoryStorage()

    with pytest.raises(ValidationError, match="25 MB"):
        await storage.put(
            scope_for(),
            ObjectKind.DOCUMENT,
            data=b"x" * (MAX_OBJECT_BYTES + 1),
            filename="big.pdf",
            content_type=PDF,
        )

    assert storage.keys == []


async def test_the_largest_allowed_file_is_accepted() -> None:
    """The boundary in the other direction, so the limit is off-by-one proof."""
    stored = await InMemoryStorage().put(
        scope_for(),
        ObjectKind.DOCUMENT,
        data=b"x" * MAX_OBJECT_BYTES,
        filename="big.pdf",
        content_type=PDF,
    )

    assert stored.size == MAX_OBJECT_BYTES


@pytest.mark.parametrize(
    "content_type",
    ["application/x-msdownload", "image/svg+xml", "text/html", "application/octet-stream", ""],
)
async def test_an_unsupported_type_is_refused(content_type: str) -> None:
    """An allowlist: storing something the pipeline cannot read is a failure
    discovered much later, by a person."""
    storage = InMemoryStorage()

    with pytest.raises(ValidationError, match="not supported"):
        await storage.put(
            scope_for(),
            ObjectKind.DOCUMENT,
            data=b"payload",
            filename="thing.pdf",
            content_type=content_type,
        )

    assert storage.keys == []


# --- tenancy ------------------------------------------------------------------


async def test_one_tenant_cannot_read_another_tenants_key() -> None:
    """The key comes out of a database row, so this should never fire — which is
    why it is here. A row pointing at another tenant must not become a download."""
    storage = InMemoryStorage()
    theirs = scope_for()
    mine = scope_for()
    stored = await storage.put(
        theirs, ObjectKind.DOCUMENT, data=b"secret", filename="a.pdf", content_type=PDF
    )

    assert await storage.get(theirs, stored.key) == b"secret"

    with pytest.raises(NotFoundError):
        await storage.get(mine, stored.key)


async def test_one_tenant_cannot_delete_or_sign_another_tenants_key() -> None:
    storage = InMemoryStorage()
    theirs = scope_for()
    mine = scope_for()
    stored = await storage.put(
        theirs, ObjectKind.DOCUMENT, data=b"secret", filename="a.pdf", content_type=PDF
    )

    with pytest.raises(NotFoundError):
        await storage.delete(mine, stored.key)
    with pytest.raises(NotFoundError):
        await storage.presigned_url(mine, stored.key)

    assert await storage.get(theirs, stored.key) == b"secret"


async def test_a_forged_key_that_merely_starts_with_the_prefix_still_needs_the_object() -> None:
    storage = InMemoryStorage()
    mine = scope_for()

    with pytest.raises(NotFoundError):
        await storage.get(mine, f"org/{mine.organization_id}/document/{uuid.uuid4()}.pdf")


# --- the rest of the interface ------------------------------------------------


async def test_a_stored_object_can_be_read_back_and_deleted() -> None:
    storage = InMemoryStorage()
    scope = scope_for()

    stored = await storage.put(
        scope, ObjectKind.DOCUMENT, data=b"hello", filename="a.txt", content_type="text/plain"
    )
    read = await storage.get(scope, stored.key)
    await storage.delete(scope, stored.key)

    assert read == b"hello"
    assert stored.content_type == "text/plain"
    assert storage.keys == []


async def test_deleting_something_that_is_gone_is_not_an_error() -> None:
    """The caller wanted it absent, and it is. Raising here turns every retry
    into a failure."""
    storage = InMemoryStorage()
    scope = scope_for()

    await storage.delete(scope, f"org/{scope.organization_id}/document/{uuid.uuid4()}.pdf")


async def test_a_presigned_url_is_capped_however_long_the_caller_asks_for() -> None:
    storage = InMemoryStorage()
    scope = scope_for()
    stored = await storage.put(
        scope, ObjectKind.DOCUMENT, data=b"x", filename="a.pdf", content_type=PDF
    )

    url = await storage.presigned_url(scope, stored.key, expires_in=86_400)

    assert "expires_in=900" in url
