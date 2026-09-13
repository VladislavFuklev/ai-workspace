"""Add external identities.

Unique on (provider, subject), not on subject alone: two providers can use
the same-looking id, and the pair is what identifies a person.

Revision ID: 4482fa83bf5d
Revises: a95e54cbfb0e
Create Date: 2026-09-13 16:23:21.817840

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4482fa83bf5d"
down_revision: str | Sequence[str] | None = "a95e54cbfb0e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "identities",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "provider",
            sa.Enum("GOOGLE", "MICROSOFT", "GITHUB", name="identity_provider"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(length=255), nullable=False),
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
            ["user_id"], ["users.id"], name=op.f("fk_identities_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_identities")),
    )
    op.create_index("ix_identities_user_id", "identities", ["user_id"], unique=False)
    op.create_index(
        "uq_identities_provider_subject", "identities", ["provider", "subject"], unique=True
    )


def downgrade() -> None:
    op.drop_index("uq_identities_provider_subject", table_name="identities")
    op.drop_index("ix_identities_user_id", table_name="identities")
    op.drop_table("identities")
