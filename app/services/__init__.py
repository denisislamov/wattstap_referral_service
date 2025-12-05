"""
Business logic services.
"""

from app.services.telegram_auth import TelegramAuthService, telegram_auth_service
from app.services.user_service import UserService, user_service
from app.services.referral_service import ReferralService, referral_service

__all__ = [
    "TelegramAuthService",
    "telegram_auth_service",
    "UserService",
    "user_service",
    "ReferralService",
    "referral_service",
]



