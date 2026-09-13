"""SQLAlchemy ORM models.

Domain tables arrive with the phases that need them — organisations in 4.1,
documents in 5.4. Every one inherits the base defined here: a naming convention
Alembic can work with, a UUID primary key, and timestamps.

Every model must be imported here, or `Base.metadata` will not know about it and
Alembic will generate a migration that drops the table.
"""

from ai_workspace_api.models.base import (
    NAMING_CONVENTION,
    Base,
    Timestamps,
    UUIDPrimaryKey,
)
from ai_workspace_api.models.session import Session
from ai_workspace_api.models.user import User

__all__ = ["NAMING_CONVENTION", "Base", "Session", "Timestamps", "UUIDPrimaryKey", "User"]
