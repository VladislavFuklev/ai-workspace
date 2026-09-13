"""Business logic and orchestration. Never imports from ``api``."""

from ai_workspace_api.services.auth import AuthService

__all__ = ["AuthService"]
