"""
API routers.
"""

from app.routers.auth import router as auth_router
from app.routers.social import router as social_router

__all__ = ["auth_router", "social_router"]


