"""The storage interface, and the rules every implementation obeys.

An abstract base class rather than a `Protocol`: the value here is not that
several classes happen to share method names, it is that *nobody can store an
object outside their own tenant's prefix*. The public methods do the checking
and the subclass implements only the transport, so a second implementation
cannot forget a rule by writing a method that merely matches a signature.

The key layout is the decision that outlives everything else here. Every object
is attributable to one organisation from its key alone:

    org/{organization_id}/{kind}/{uuid}{extension}

which means a mistake is visible in a bucket listing, not only in a join.
"""

from __future__ import annotations

import re
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum

from ai_workspace_api.core.errors import NotFoundError, ValidationError
from ai_workspace_api.core.tenancy import TenantScope

# Enough for the documents this product is for, small enough that one request
# cannot exhaust the process. Enforced here as well as at the HTTP layer (5.3):
# the boundary check protects the endpoint, this one protects the bucket.
MAX_OBJECT_BYTES = 25 * 1024 * 1024

# What the pipeline in 5.6 can actually read. An allowlist, not a denylist:
# storing something unreadable is a failure discovered much later, by a user.
ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/markdown",
        "text/plain",
    }
)

# A conservative extension: letters and digits only, so nothing in a key can be
# read as a path segment, a query string or a shell argument.
_EXTENSION = re.compile(r"^\.[a-z0-9]{1,8}$")

PRESIGNED_URL_MAX_SECONDS = 15 * 60

EMPTY_FILE = "That file is empty."
TOO_LARGE = "That file is larger than 25 MB."
UNSUPPORTED_TYPE = "That file type is not supported."


class ObjectKind(StrEnum):
    """What an object is, as a path segment.

    Named rather than free text so a listing groups by purpose, and so a typo is
    a type error instead of a second parallel prefix nobody notices.
    """

    DOCUMENT = "document"
    # Text pulled out of a document (task 5.6). Kept beside the original: it is
    # derived from it, expires with it, and belongs to the same tenant.
    EXTRACTION = "extraction"


@dataclass(frozen=True, slots=True)
class StoredObject:
    key: str
    size: int
    content_type: str


def tenant_prefix(scope: TenantScope) -> str:
    return f"org/{scope.organization_id}/"


def build_key(scope: TenantScope, kind: ObjectKind, filename: str) -> str:
    """A key the caller cannot influence beyond the file extension.

    The name someone uploaded is not part of the key. It may contain anything at
    all — separators, control characters, another tenant's id — and it is theirs
    to choose, so it belongs in a database column, not in a path. Only the
    extension survives, and only if it looks like one.
    """
    suffix = filename[filename.rfind(".") :].lower() if "." in filename else ""
    extension = suffix if _EXTENSION.match(suffix) else ""
    return f"{tenant_prefix(scope)}{kind.value}/{uuid.uuid4()}{extension}"


class Storage(ABC):
    """Object storage, scoped to a tenant on every call.

    Every method takes a `TenantScope` — which only a verified membership can
    produce (ADR-021) — and refuses a key belonging to anyone else with
    `NotFoundError`, the same answer the rest of the API gives for another
    tenant's data.
    """

    async def put(
        self, scope: TenantScope, kind: ObjectKind, *, data: bytes, filename: str, content_type: str
    ) -> StoredObject:
        """Stores bytes and returns where they went.

        The content type is validated rather than trusted: it arrives from the
        client, and a browser will happily label a PDF as anything.
        """
        if not data:
            raise ValidationError(EMPTY_FILE, detail=[{"field": "file", "message": EMPTY_FILE}])
        if len(data) > MAX_OBJECT_BYTES:
            raise ValidationError(TOO_LARGE, detail=[{"field": "file", "message": TOO_LARGE}])
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValidationError(
                UNSUPPORTED_TYPE, detail=[{"field": "file", "message": UNSUPPORTED_TYPE}]
            )

        key = build_key(scope, kind, filename)
        await self._put(key, data, content_type)
        return StoredObject(key=key, size=len(data), content_type=content_type)

    async def get(self, scope: TenantScope, key: str) -> bytes:
        return await self._get(self._own(scope, key))

    async def delete(self, scope: TenantScope, key: str) -> None:
        await self._delete(self._own(scope, key))

    async def presigned_url(self, scope: TenantScope, key: str, *, expires_in: int = 300) -> str:
        """A time-limited URL the browser can fetch directly.

        Capped: a link that outlives the session it was made for is a link that
        can be forwarded, and nothing about the object's own permissions is
        re-checked when it is used.
        """
        return await self._presigned_url(
            self._own(scope, key), min(expires_in, PRESIGNED_URL_MAX_SECONDS)
        )

    @abstractmethod
    async def check(self) -> None:
        """Raises if the store is unreachable. Used by the readiness probe."""

    def _own(self, scope: TenantScope, key: str) -> str:
        """The key belongs to this tenant, or it does not exist as far as they know.

        Keys come out of the database, so this should never fire — which is the
        reason it is here. A row pointing at another tenant's object is exactly
        the bug that must not become a download.
        """
        if not key.startswith(tenant_prefix(scope)):
            raise NotFoundError("That file does not exist.")
        return key

    @abstractmethod
    async def _put(self, key: str, data: bytes, content_type: str) -> None: ...

    @abstractmethod
    async def _get(self, key: str) -> bytes: ...

    @abstractmethod
    async def _delete(self, key: str) -> None: ...

    @abstractmethod
    async def _presigned_url(self, key: str, expires_in: int) -> str: ...
