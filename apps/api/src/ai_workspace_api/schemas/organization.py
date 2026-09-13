"""Organisation and membership shapes."""

from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import BaseModel, Field

from ai_workspace_api.models import Role


class CreateOrganizationRequest(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=120)]


class OrganizationSummary(BaseModel):
    """An organisation as a member sees it, with their own role in it."""

    id: uuid.UUID
    name: str
    slug: str
    role: Role

    model_config = {"from_attributes": True}


class MemberSummary(BaseModel):
    user_id: uuid.UUID
    email: str
    display_name: str
    role: Role
