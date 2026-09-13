"""Creating organisations."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.core.errors import ValidationError
from ai_workspace_api.core.logging import get_logger
from ai_workspace_api.core.slugs import slugify, unique_suffix
from ai_workspace_api.models import Organization
from ai_workspace_api.repositories.organization import OrganizationRepository

logger = get_logger(__name__)

# Enough attempts that a collision is vanishingly unlikely, few enough that a
# pathological name fails fast instead of looping.
SLUG_ATTEMPTS = 5

UNUSABLE_NAME = "Enter a name with at least one letter or number."


class OrganizationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._organizations = OrganizationRepository(session)

    async def create(self, name: str) -> Organization:
        """Creates an organisation with a slug derived from its name."""
        cleaned = name.strip()
        organization = Organization(name=cleaned, slug=await self._available_slug(cleaned))
        self._organizations.add(organization)
        await self._session.flush()
        logger.info("organization created", organization_id=str(organization.id))
        return organization

    async def _available_slug(self, name: str) -> str:
        base = slugify(name)
        if not base:
            # "..." or "!!!" leaves nothing addressable. Rejected rather than
            # replaced with something invented.
            raise ValidationError(
                UNUSABLE_NAME, detail=[{"field": "name", "message": UNUSABLE_NAME}]
            )

        if not await self._organizations.slug_exists(base):
            return base

        for _ in range(SLUG_ATTEMPTS):
            candidate = f"{base[:55]}-{unique_suffix()}"
            if not await self._organizations.slug_exists(candidate):
                return candidate

        # Five random suffixes all colliding means something is wrong that
        # retrying will not fix.
        raise ValidationError(
            "Could not create an address for that name. Try a different one.",
            detail=[{"field": "name", "message": "That name is not available."}],
        )
