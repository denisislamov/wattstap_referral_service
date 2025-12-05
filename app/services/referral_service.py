"""
Referral service for managing referral system.
"""

from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.friendship import Friendship
from app.schemas.auth import ReferralResult, ReferrerInfo
from app.config import settings


class ReferralService:
    """
    Service for referral system operations.
    
    Handles applying referral codes, creating friendships,
    and calculating referral bonuses.
    """
    
    @property
    def bonus_per_referral(self) -> int:
        """Bonus watts given for each successful referral."""
        return settings.referral_bonus_watts
    
    async def can_apply_referral(
        self, 
        db: AsyncSession, 
        new_user_telegram_id: int, 
        referrer: User
    ) -> Tuple[bool, str]:
        """
        Check if a referral code can be applied.
        
        Args:
            db: Database session
            new_user_telegram_id: Telegram ID of the new user
            referrer: User who owns the referral code
            
        Returns:
            Tuple of (can_apply, reason)
        """
        # Cannot invite yourself
        if referrer.telegram_id == new_user_telegram_id:
            return False, "Cannot use your own referral code"
        
        # Check if user already exists (referral only works for new users)
        result = await db.execute(
            select(User.id).where(User.telegram_id == new_user_telegram_id)
        )
        if result.scalar_one_or_none():
            return False, "Referral code can only be applied on first login"
        
        return True, "OK"
    
    async def apply_referral(
        self, 
        db: AsyncSession, 
        new_user: User, 
        referrer: User
    ) -> ReferralResult:
        """
        Apply a referral code for a new user.
        
        This will:
        1. Set referred_by for the new user
        2. Create mutual friendship
        3. Give bonus watts to the referrer
        
        Args:
            db: Database session
            new_user: The newly registered user
            referrer: The user who referred them
            
        Returns:
            ReferralResult with details
        """
        try:
            # 1. Set who referred the new user
            new_user.referred_by_id = referrer.id
            
            # 2. Create mutual friendship
            # Referrer -> New User
            friendship1 = Friendship(
                user_id=referrer.id,
                friend_id=new_user.id,
                source="referral"
            )
            # New User -> Referrer
            friendship2 = Friendship(
                user_id=new_user.id,
                friend_id=referrer.id,
                source="referral"
            )
            db.add(friendship1)
            db.add(friendship2)
            
            # 3. Give bonus to referrer
            referrer.watts += self.bonus_per_referral
            
            await db.flush()
            
            return ReferralResult(
                applied=True,
                referrer=ReferrerInfo(
                    user_id=referrer.telegram_id,
                    nickname=referrer.display_name,
                    avatar_url=referrer.photo_url,
                    level=referrer.level
                ),
                bonus_for_referrer=self.bonus_per_referral,
                message=f"You were invited by {referrer.display_name}!"
            )
            
        except Exception as e:
            return ReferralResult(
                applied=False,
                message=f"Failed to apply referral: {str(e)}"
            )
    
    async def get_friends(
        self, 
        db: AsyncSession, 
        user: User
    ) -> list[Tuple[User, Friendship]]:
        """
        Get all friends of a user.
        
        Args:
            db: Database session
            user: User to get friends for
            
        Returns:
            List of (friend_user, friendship) tuples
        """
        result = await db.execute(
            select(User, Friendship)
            .join(Friendship, Friendship.friend_id == User.id)
            .where(Friendship.user_id == user.id)
            .order_by(Friendship.created_at.desc())
        )
        return result.all()
    
    async def get_friends_count(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> int:
        """
        Get count of user's friends.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Number of friends
        """
        result = await db.execute(
            select(func.count(Friendship.id))
            .where(Friendship.user_id == user_id)
        )
        return result.scalar() or 0
    
    async def get_referral_stats(
        self, 
        db: AsyncSession, 
        user: User
    ) -> dict:
        """
        Get referral statistics for a user.
        
        Args:
            db: Database session
            user: User to get stats for
            
        Returns:
            Dictionary with referral statistics
        """
        # Count users referred by this user
        result = await db.execute(
            select(func.count(User.id))
            .where(User.referred_by_id == user.id)
        )
        invited_count = result.scalar() or 0
        
        # Calculate total bonus earned
        total_bonus = invited_count * self.bonus_per_referral
        
        return {
            "total_friends_invited": invited_count,
            "total_bonus_earned": total_bonus,
            "bonus_per_friend": self.bonus_per_referral
        }
    
    async def check_friendship_exists(
        self, 
        db: AsyncSession, 
        user_id: int, 
        friend_id: int
    ) -> bool:
        """
        Check if a friendship already exists.
        
        Args:
            db: Database session
            user_id: First user ID
            friend_id: Second user ID
            
        Returns:
            True if friendship exists
        """
        result = await db.execute(
            select(Friendship.id)
            .where(Friendship.user_id == user_id)
            .where(Friendship.friend_id == friend_id)
        )
        return result.scalar_one_or_none() is not None


# Singleton instance
referral_service = ReferralService()


