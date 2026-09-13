"""Creating, renaming and ending organisations."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ai_workspace_api.core.errors import NotFoundError, ValidationError
from ai_workspace_api.core.logging import get_logger
from ai_workspace_api.core.permissions import Permission
from ai_workspace_api.core.slugs import RESERVED, slugify, unique_suffix
from ai_workspace_api.core.tenancy import TenantScope
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

    async def rename(self, scope: TenantScope, name: str) -> Organization:
        """Changes the display name. The address never changes.

        A slug that followed the name would break every link anyone has shared,
        every bookmark, and the organisation each browser remembers — silently,
        because the old address would then belong to nobody. The name is what
        people read; the slug is an identifier that happens to be legible.
        """
        scope.require(Permission.ORGANIZATION_UPDATE)

        organization = await self._require(scope)
        cleaned = name.strip()
        if not cleaned:
            raise ValidationError(
                UNUSABLE_NAME, detail=[{"field": "name", "message": UNUSABLE_NAME}]
            )

        organization.name = cleaned
        await self._session.flush()
        logger.info("organization renamed", organization_id=str(organization.id))
        return organization

    async def delete(self, scope: TenantScope) -> None:
        """Ends the organisation.

        Memberships go with it: the foreign key is `ON DELETE CASCADE`, so there
        is no window in which a membership points at nothing. Documents will
        follow the same way in phase 5.
        """
        scope.require(Permission.ORGANIZATION_DELETE)

        organization = await self._require(scope)
        await self._session.delete(organization)
        await self._session.flush()
        logger.info(
            "organization deleted",
            organization_id=str(organization.id),
            actor_id=str(scope.user_id),
        )

    async def _require(self, scope: TenantScope) -> Organization:
        organization = await self._organizations.get_by_id(scope.organization_id)
        if organization is None:
            # Unreachable: the scope was resolved from this organisation. A
            # check rather than an assert, which `python -O` strips.
            raise NotFoundError("That workspace does not exist.")
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
