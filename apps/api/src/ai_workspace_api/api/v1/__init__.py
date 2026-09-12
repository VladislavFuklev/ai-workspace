"""Version 1 of the HTTP API.

A new major version becomes a sibling package with its own router, so v1 keeps
working unchanged while v2 exists. Versioning by URL prefix rather than by header:
it is visible in a log line, a bug report and a browser address bar, which is
worth more here than header purity.
"""

from ai_workspace_api.api.v1.router import api_router

__all__ = ["api_router"]
