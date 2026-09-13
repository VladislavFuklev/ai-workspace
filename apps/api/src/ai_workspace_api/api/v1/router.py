"""The v1 router.

Every versioned endpoint is mounted here, so `create_app` includes one router and
the set of routes in a version is readable in one file.

Health endpoints are deliberately absent: an orchestrator's probe URL should not
change when the API version does.
"""

from fastapi import APIRouter

from ai_workspace_api.api.v1.routes import auth, organizations, password_reset

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(password_reset.router)
api_router.include_router(organizations.router)

# Routers arrive with their phases:
#   organizations — phase 4
#   documents     — phase 5
#   search        — phase 6
#   conversations — phase 7
#   usage         — phase 10
