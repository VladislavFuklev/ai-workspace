"""Organisation and membership shapes."""

from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import BaseModel, Field

from ai_workspace_api.core.permissions import Permission, permissions_for
from ai_workspace_api.models import Organization, Role


class CreateOrganizationRequest(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=120)]


class UpdateOrganizationRequest(BaseModel):
    """Only the name. The slug is fixed at creation — see `OrganizationService.rename`."""

    name: Annotated[str, Field(min_length=1, max_length=120)]


class ChangeRoleRequest(BaseModel):
    role: Role


class OrganizationSummary(BaseModel):
    """An organisation as a member sees it, with their own role in it.

    `permissions` is what that role may do here, sent so a client can hide an
    action it would be refused. The alternative — a copy of the permission table
    in the web app — is a copy that drifts, and every drift shows up as a button
    that fails when pressed. The list is a convenience for rendering; the API
    still checks every request.
    """

    id: uuid.UUID
    name: str
    slug: str
    role: Role
    permissions: list[Permission]

    model_config = {"from_attributes": True}

    @classmethod
    def of(cls, organization: Organization, role: Role) -> OrganizationSummary:
        return cls(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            role=role,
            permissions=sorted(permissions_for(role)),
        )


class MemberSummary(BaseModel):
    user_id: uuid.UUID
    email: str
    display_name: str
    role: Role
