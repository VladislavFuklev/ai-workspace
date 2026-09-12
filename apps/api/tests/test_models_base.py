"""The base every table inherits: naming, identity, timestamps."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from ai_workspace_api.core.database import create_engine, create_session_factory
from ai_workspace_api.core.settings import Settings
from ai_workspace_api.models import Base, Timestamps, UUIDPrimaryKey

from .conftest import BuildSettings


class Sample(Base, UUIDPrimaryKey, Timestamps):
    """A throwaway table, so the base is exercised without inventing a domain."""

    __tablename__ = "base_probe"
    __table_args__ = (UniqueConstraint("label"),)

    label: Mapped[str] = mapped_column(String(50))


SAMPLE_TABLE = Base.metadata.tables["base_probe"]


def test_primary_key_is_a_uuid_with_an_application_default() -> None:
    """The default runs at flush, not at construction — SQLAlchemy column
    defaults are applied on insert. What matters is that it is the application
    supplying it, not a server-side function that a fixture might not have."""
    # Via metadata rather than __table__: the declarative attribute is typed as
    # FromClause, which has no .constraints and is not a Table.
    column = SAMPLE_TABLE.c.id

    assert column.primary_key
    assert column.type.python_type is uuid.UUID
    assert column.default is not None, "the application must supply the id"
    assert column.server_default is None, "no server-side function to depend on"


def test_constraints_follow_the_naming_convention() -> None:
    """Unnamed constraints cannot be dropped by a later migration."""
    names = {c.name for c in SAMPLE_TABLE.constraints if c.name}

    assert "pk_base_probe" in names
    assert "uq_base_probe_label" in names
    assert all(name is not None for name in names)


@pytest.mark.integration
async def test_timestamps_are_set_by_the_database(
    valid_env: dict[str, str], settings_from: BuildSettings, database_url: str
) -> None:
    settings: Settings = settings_from({**valid_env, "DATABASE_URL": database_url})
    engine = create_engine(settings)
    factory = create_session_factory(engine)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all, tables=[SAMPLE_TABLE])

        async with factory() as session:
            row = Sample(label="written")
            session.add(row)
            await session.commit()
            # expire_on_commit=False means these are readable without a refresh.
            assert row.created_at is not None
            assert row.created_at.tzinfo is not None, "timestamps must be timezone-aware"
            # A window, not `<= now()`: this compares the database's clock with
            # this process's, and they differ by milliseconds. A strict
            # inequality here is a test that fails a few times a day for no
            # reason. The window is still tight enough to catch a wrong value —
            # an epoch date, or a naive timestamp read as UTC.
            assert abs(row.created_at - datetime.now(UTC)) < timedelta(minutes=1)
            assert row.updated_at == row.created_at
            assert isinstance(row.id, uuid.UUID), "the default produced an id at flush"
    finally:
        async with engine.begin() as connection:
            await connection.execute(text("DROP TABLE IF EXISTS base_probe"))
        await engine.dispose()
