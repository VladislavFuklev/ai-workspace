"""Creating organisations."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.core.errors import ValidationError
from ai_workspace_api.core.logging import get_logger
from ai_workspace_api.core.slugs import RESERVED, slugify, unique_suffix
from ai_workspace_api.models import Organization, Role, User
from ai_workspace_api.repositories.organization import OrganizationRepository
from ai_workspace_api.services.membership import MembershipService

logger = get_logger(__name__)

# Enough attempts that a collision is vanishingly unlikely, few enough that a
# pathological name fails fast instead of looping.
SLUG_ATTEMPTS = 5

UNUSABLE_NAME = "Enter a name with at least one letter or number."


class OrganizationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._organizations = OrganizationRepository(session)
        self._memberships = MembershipService(session)

    async def create(self, name: str, owner: User) -> Organization:
        """Creates an organisation and makes its creator the owner.

        One transaction, because an organisation with no members is unreachable
        by anyone — including the person who just made it — and nothing in the
        product could fix it.
        """
        cleaned = name.strip()
        organization = Organization(name=cleaned, slug=await self._available_slug(cleaned))
        self._organizations.add(organization)
        await self._session.flush()

        self._memberships.add_member(organization, owner, Role.OWNER)
        await self._session.flush()

        logger.info(
            "organization created",
            organization_id=str(organization.id),
            owner_id=str(owner.id),
        )
        return organization

    async def _available_slug(self, name: str) -> str:
        base = slugify(name)
        if not base:
            # "..." or "!!!" leaves nothing addressable. Rejected rather than
            # replaced with something invented.
            raise ValidationError(
                UNUSABLE_NAME, detail=[{"field": "name", "message": UNUSABLE_NAME}]
            )

        # A reserved slug is treated exactly like a taken one: the organisation
        # is still created, under a suffixed address, rather than the person
        # being told their company name is not allowed.
        if base not in RESERVED and not await self._organizations.slug_exists(base):
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
