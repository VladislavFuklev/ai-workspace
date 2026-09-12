"""Shared FastAPI dependencies.

Everything a handler needs arrives through these, so a test overrides one
dependency instead of patching a module.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from ai_workspace_api.core.settings import Settings


def get_app_settings(request: Request) -> Settings:
    """The settings the app was built with — not the module-level singleton."""
    settings: Settings = request.app.state.settings
    return settings


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
