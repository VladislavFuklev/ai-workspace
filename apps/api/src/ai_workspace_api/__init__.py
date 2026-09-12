"""AI Workspace API.

Layer boundaries (see docs/ARCHITECTURE.md):

    api -> services -> repositories -> models

Routers hold no business logic, services never import routers, and all
provider-specific AI code lives under ``ai`` behind an interface.
"""

__all__ = ["__version__"]

__version__ = "0.0.0"
