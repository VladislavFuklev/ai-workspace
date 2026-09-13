"""Add memberships.

Unique on (user_id, organization_id): two rows would mean two roles for one
person in one organisation, and every permission check would have to decide
which of them wins.

Revision ID: 743a5759a742
Revises: b30f404c533c
Create Date: 2026-09-13 16:49:42.730172

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "743a5759a742"
down_revision: str | Sequence[str] | None = "b30f404c533c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "memberships",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("OWNER", "ADMIN", "MEMBER", "VIEWER", name="membership_role"),
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_memberships_organization_id_organizations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_memberships_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memberships")),
    )
    op.create_index(
        "ix_memberships_organization_id", "memberships", ["organization_id"], unique=False
    )
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"], unique=False)
    op.create_index(
        "uq_memberships_user_organization",
        "memberships",
        ["user_id", "organization_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_memberships_user_organization", table_name="memberships")
    op.drop_index("ix_memberships_user_id", table_name="memberships")
    op.drop_index("ix_memberships_organization_id", table_name="memberships")
    op.drop_table("memberships")
