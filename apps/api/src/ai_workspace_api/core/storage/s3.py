"""S3-compatible storage: MinIO in development, S3 or R2 in production.

One client for the process, opened at startup. A client per request would mean a
TLS handshake and credential resolution per request, and aiobotocore's client is
an async context manager precisely because it owns a connection pool.

Every failure is translated: a caller should handle `NotFoundError` and
`ServiceUnavailableError`, not `ClientError` with a string code inside it.
"""

from __future__ import annotations

from contextlib import AsyncExitStack

import aioboto3
from aiobotocore.config import AioConfig
from botocore.exceptions import BotoCoreError, ClientError
from types_aiobotocore_s3.client import S3Client

from ai_workspace_api.core.errors import NotFoundError, ServiceUnavailableError
from ai_workspace_api.core.logging import get_logger
from ai_workspace_api.core.settings import Settings

from .base import Storage

logger = get_logger(__name__)

STORE_UNAVAILABLE = "File storage is unavailable. Try again in a moment."

# Bounded, so a hung store surfaces as an error rather than as a request that
# never returns. Retries are botocore's own, on the codes worth retrying.
_CONFIG = AioConfig(
    connect_timeout=5,
    read_timeout=30,
    retries={"max_attempts": 3, "mode": "standard"},
    # MinIO does not do virtual-host style addressing without DNS per bucket.
    s3={"addressing_style": "path"},
)


class S3Storage(Storage):
    def __init__(self, client: S3Client, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    async def check(self) -> None:
        try:
            await self._client.head_bucket(Bucket=self._bucket)
        except (BotoCoreError, ClientError) as error:
            raise ServiceUnavailableError(STORE_UNAVAILABLE) from error

    async def _put(self, key: str, data: bytes, content_type: str) -> None:
        try:
            await self._client.put_object(
                Bucket=self._bucket, Key=key, Body=data, ContentType=content_type
            )
        except (BotoCoreError, ClientError) as error:
            logger.warning("storage put failed", key=key, exc_info=error)
            raise ServiceUnavailableError(STORE_UNAVAILABLE) from error

    async def _get(self, key: str) -> bytes:
        try:
            response = await self._client.get_object(Bucket=self._bucket, Key=key)
            async with response["Body"] as stream:
                return await stream.read()
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") in {"NoSuchKey", "404"}:
                raise NotFoundError("That file does not exist.") from error
            logger.warning("storage get failed", key=key, exc_info=error)
            raise ServiceUnavailableError(STORE_UNAVAILABLE) from error
        except BotoCoreError as error:
            logger.warning("storage get failed", key=key, exc_info=error)
            raise ServiceUnavailableError(STORE_UNAVAILABLE) from error

    async def _delete(self, key: str) -> None:
        try:
            await self._client.delete_object(Bucket=self._bucket, Key=key)
        except (BotoCoreError, ClientError) as error:
            logger.warning("storage delete failed", key=key, exc_info=error)
            raise ServiceUnavailableError(STORE_UNAVAILABLE) from error

    async def _presigned_url(self, key: str, expires_in: int) -> str:
        # Signing is arithmetic, not a request: no network, nothing to fail
        # slowly, and no reason for the URL to be wrong if the store is down.
        return await self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )


async def open_s3_storage(settings: Settings, stack: AsyncExitStack) -> S3Storage:
    """Opens the client for the life of the application.

    The exit stack belongs to the lifespan, so the client is closed on shutdown
    even if something started after it fails to start.
    """
    session = aioboto3.Session()
    client = await stack.enter_async_context(
        session.client(
            "s3",
            endpoint_url=str(settings.s3_endpoint_url),
            aws_access_key_id=settings.s3_access_key.get_secret_value(),
            aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
            region_name=settings.s3_region,
            config=_CONFIG,
        )
    )
    return S3Storage(client, settings.s3_bucket)
