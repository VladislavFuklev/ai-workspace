"""Enable the pgvector extension.

The compose stack creates it from an init script (task 0.3) and CI from
`scripts/enable_pgvector.py`. Neither covers a managed database or a fresh
deployment, so the migration is the one path every environment takes.

Creating an extension needs elevated rights. On a managed Postgres the migration
role must have them, or an operator installs it once by hand — which
`IF NOT EXISTS` already makes safe.

Revision ID: 2b536be08293
Revises:
Create Date: 2026-09-13
"""

from collections.abc import Sequence

from alembic import op

revision: str = "2b536be08293"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Deliberately empty.

    Dropping the extension would take every vector column with it, and other
    schemas in the same database may depend on it. An irreversible step is
    better stated than pretended.
    """
