"""Create the vector extension in the configured database.

The compose stack does this from an init script (task 0.3), but a CI service
container has no init hook. Task 2.5 will also handle it in a migration, for
environments built from neither.
"""

from __future__ import annotations

import asyncio
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def main() -> None:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    try:
        async with engine.begin() as connection:
            await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
