"""
Pydantic schemas for request/response validation.
"""

from app.schemas.auth import (
    TelegramAuthRequest,
    AuthResponse,
    PlayerInfo,
    ReferralResult,
    ReferrerInfo,
)
from app.schemas.social import (
    FriendInfo,
    FriendsListResponse,
    MyReferralResponse,
)
from app.schemas.common import (
    SuccessResponse,
    ErrorResponse,
    ErrorDetail,
)
from app.schemas.progress import (
    PlayerProgress,
    SaveProgressRequest,
    SaveProgressResponse,
    LoadProgressResponse,
    ResetProgressRequest,
    ResetProgressResponse,
)

__all__ = [
    # Auth
    "TelegramAuthRequest",
    "AuthResponse",
    "PlayerInfo",
    "ReferralResult",
    "ReferrerInfo",
    # Social
    "FriendInfo",
    "FriendsListResponse",
    "MyReferralResponse",
    # Common
    "SuccessResponse",
    "ErrorResponse",
    "ErrorDetail",
    # Progress
    "PlayerProgress",
    "SaveProgressRequest",
    "SaveProgressResponse",
    "LoadProgressResponse",
    "ResetProgressRequest",
    "ResetProgressResponse",
]



