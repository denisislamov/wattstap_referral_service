"""
API routers.
"""

from app.routers.auth import router as auth_router
from app.routers.social import router as social_router
from app.routers.progress import router as progress_router
from app.routers.mining_balance import router as mining_balance_router
from app.routers.avatar import router as avatar_router

__all__ = ["auth_router", "social_router", "progress_router", "mining_balance_router", "avatar_router"]


