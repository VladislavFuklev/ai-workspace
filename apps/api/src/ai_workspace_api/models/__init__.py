"""SQLAlchemy ORM models.

Domain tables arrive with the phases that need them — users in 3.1, organisations
in 4.1, documents in 5.4. What lives here now is the base every one of them
inherits: a naming convention Alembic can work with, a UUID primary key, and
timestamps.

Every model must be imported here, or `Base.metadata` will not know about it and
Alembic will generate a migration that drops the table.
"""

from ai_workspace_api.models.base import (
    NAMING_CONVENTION,
    Base,
    Timestamps,
    UUIDPrimaryKey,
)

__all__ = ["NAMING_CONVENTION", "Base", "Timestamps", "UUIDPrimaryKey"]
