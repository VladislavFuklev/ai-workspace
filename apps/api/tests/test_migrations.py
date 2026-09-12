"""Migrations: linear history, and no drift between models and schema."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection

from ai_workspace_api.core.database import create_engine
from ai_workspace_api.models import Base

from .conftest import BuildSettings

API_ROOT = Path(__file__).resolve().parents[1]


def alembic_config() -> Config:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "migrations"))
    return config


def test_history_has_a_single_head() -> None:
    """Two heads mean two branches nobody merged, and `upgrade head` then fails."""
    heads = ScriptDirectory.from_config(alembic_config()).get_heads()

    assert len(heads) == 1, f"expected one head, found {heads}"


def test_every_revision_declares_a_downgrade() -> None:
    """A downgrade may be a documented no-op, but it must be a decision."""
    script = ScriptDirectory.from_config(alembic_config())

    for revision in script.walk_revisions():
        source = Path(revision.path).read_text()
        assert "def downgrade()" in source, f"{revision.revision} has no downgrade"


@pytest.mark.integration
async def test_models_and_schema_do_not_drift(
    valid_env: dict[str, str], settings_from: BuildSettings, database_url: str
) -> None:
    """After `alembic upgrade head`, autogenerate must find nothing to do.

    This is the check that catches the common failure: a model changed and nobody
    wrote the migration. It compares what the database has against what the
    metadata describes — the same comparison autogenerate would make.
    """
    settings = settings_from({**valid_env, "DATABASE_URL": database_url})
    engine = create_engine(settings)

    def diff(connection: Connection) -> list[object]:
        context = MigrationContext.configure(
            connection, opts={"compare_type": True, "compare_server_default": True}
        )
        # `include_object` keeps the comparison to tables this project defines:
        # the database is shared, and another schema's table is not drift here.
        defined = set(Base.metadata.tables)
        return [
            change
            for change in compare_metadata(context, Base.metadata)
            if any(name in repr(change) for name in defined)
        ]

    try:
        async with engine.connect() as connection:
            changes = await connection.run_sync(diff)
    finally:
        await engine.dispose()

    assert changes == [], f"models and migrations have drifted: {changes}"


@pytest.mark.integration
async def test_the_drift_check_can_actually_fail(
    valid_env: dict[str, str], settings_from: BuildSettings, database_url: str
) -> None:
    """The check above is vacuous until a model exists — prove it detects one.

    A table added to the metadata but not to any migration is exactly the failure
    the check is for, so it is introduced here on purpose and torn down after.
    """
    from sqlalchemy import Column, Integer, Table

    settings = settings_from({**valid_env, "DATABASE_URL": database_url})
    engine = create_engine(settings)
    Table("drift_probe", Base.metadata, Column("id", Integer, primary_key=True))

    def diff(connection: Connection) -> list[object]:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        return [
            change
            for change in compare_metadata(context, Base.metadata)
            if "drift_probe" in repr(change)
        ]

    try:
        async with engine.connect() as connection:
            changes = await connection.run_sync(diff)
        assert changes, "a table missing from every migration went undetected"
    finally:
        Base.metadata.remove(Base.metadata.tables["drift_probe"])
        await engine.dispose()
