"""Add organizations.

The tenant boundary. Slug uniqueness is case-insensitive for the same reason as
user email: `acme` and `Acme` in a URL would be two tenants that look like one.

Revision ID: b30f404c533c
Revises: 4482fa83bf5d
Create Date: 2026-09-13 16:47:05.674446

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b30f404c533c"
down_revision: str | Sequence[str] | None = "4482fa83bf5d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=60), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organizations")),
    )
    op.create_index(
        "uq_organizations_slug_lower",
        "organizations",
        [sa.literal_column("lower(slug)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_organizations_slug_lower", table_name="organizations")
    op.drop_table("organizations")
