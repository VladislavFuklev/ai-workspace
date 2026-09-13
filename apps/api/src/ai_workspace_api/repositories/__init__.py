"""Data access. The only layer that talks to the database directly.

A repository never commits: the service layer owns the transaction boundary, and
a repository that commits makes a partial write impossible to reason about
(task 2.3).
"""

from ai_workspace_api.repositories.membership import MembershipRepository
from ai_workspace_api.repositories.organization import OrganizationRepository
from ai_workspace_api.repositories.session import SessionRepository
from ai_workspace_api.repositories.user import UserRepository, normalize_email

__all__ = [
    "MembershipRepository",
    "OrganizationRepository",
    "SessionRepository",
    "UserRepository",
    "normalize_email",
]
