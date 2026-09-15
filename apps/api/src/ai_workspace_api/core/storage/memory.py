"""Storage that lives in a dictionary.

Not a mock: it is the same class hierarchy, so it enforces the same size, type
and tenant rules, and a test that passes against it is testing the rules rather
than a stand-in that agrees with them. What it does not test is S3 itself, which
is what the integration test against MinIO is for.

Also the reason the unit suite runs with no network at all.
"""

from __future__ import annotations

from ai_workspace_api.core.errors import NotFoundError

from .base import Storage


class InMemoryStorage(Storage):
    def __init__(self) -> None:
        self._objects: dict[str, tuple[bytes, str]] = {}

    @property
    def keys(self) -> list[str]:
        """For assertions: what is actually stored, in insertion order."""
        return list(self._objects)

    async def check(self) -> None:
        return None

    async def _put(self, key: str, data: bytes, content_type: str) -> None:
        self._objects[key] = (data, content_type)

    async def _get(self, key: str) -> bytes:
        stored = self._objects.get(key)
        if stored is None:
            raise NotFoundError("That file does not exist.")
        return stored[0]

    async def _delete(self, key: str) -> None:
        # Deleting something that is not there is the outcome the caller wanted.
        self._objects.pop(key, None)

    async def _presigned_url(self, key: str, expires_in: int) -> str:
        return f"memory://{key}?expires_in={expires_in}"
