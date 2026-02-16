"""
Business logic services.
"""

from app.services.telegram_auth import TelegramAuthService, telegram_auth_service
from app.services.user_service import UserService, user_service
from app.services.referral_service import ReferralService, referral_service
from app.services.progress_service import ProgressService, progress_service
from app.services.mining_balance_service import MiningBalanceService, mining_balance_service

__all__ = [
    "TelegramAuthService",
    "telegram_auth_service",
    "UserService",
    "user_service",
    "ReferralService",
    "referral_service",
    "ProgressService",
    "progress_service",
    "MiningBalanceService",
    "mining_balance_service",
]



