"""
Avatar service for managing avatar purchases and unlocks.
"""

from typing import Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class AvatarService:
    """
    Service for avatar purchase and unlock operations.
    
    Handles server-side validation of avatar purchases,
    ensuring the player has enough currency and meets level requirements.
    """
    
    def _get_unlocked_avatars(self, user: User) -> List[str]:
        """Parse the unlocked_avatars string into a list."""
        if not user.unlocked_avatars:
            return []
        return [aid.strip() for aid in user.unlocked_avatars.split(",") if aid.strip()]
    
    def _set_unlocked_avatars(self, user: User, avatars: List[str]) -> None:
        """Save the list of unlocked avatars as a comma-separated string."""
        user.unlocked_avatars = ",".join(avatars)
    
    def _is_avatar_unlocked(self, user: User, avatar_id: str) -> bool:
        """Check if an avatar is already unlocked."""
        return avatar_id in self._get_unlocked_avatars(user)
    
    async def purchase_avatar(
        self,
        db: AsyncSession,
        user: User,
        avatar_id: str,
        price: int,
        currency: str = "watts"
    ) -> Tuple[bool, int, List[str], str]:
        """
        Purchase an avatar with currency.
        
        Server-side validation:
        - Check avatar is not already unlocked
        - Check player has enough currency
        - Deduct currency and add avatar to unlocked list
        
        Args:
            db: Database session
            user: User making the purchase
            avatar_id: ID of the avatar to purchase
            price: Expected price (validated on server side)
            currency: Currency type ('watts')
            
        Returns:
            Tuple of (success, new_watts_balance, unlocked_avatars, message)
        """
        try:
            if not avatar_id:
                return False, user.watts, self._get_unlocked_avatars(user), "Avatar ID is required"
            
            if currency != "watts":
                return False, user.watts, self._get_unlocked_avatars(user), f"Currency '{currency}' is not supported"
            
            if price < 0:
                return False, user.watts, self._get_unlocked_avatars(user), "Price cannot be negative"
            
            # Check if already unlocked
            if self._is_avatar_unlocked(user, avatar_id):
                return False, user.watts, self._get_unlocked_avatars(user), f"Avatar '{avatar_id}' is already unlocked"
            
            # Check if player has enough watts
            if user.watts < price:
                return False, user.watts, self._get_unlocked_avatars(user), \
                    f"Not enough watts. Have: {user.watts}, need: {price}"
            
            # Deduct currency
            user.watts -= price
            
            # Add avatar to unlocked list
            unlocked = self._get_unlocked_avatars(user)
            unlocked.append(avatar_id)
            self._set_unlocked_avatars(user, unlocked)
            
            await db.flush()
            await db.refresh(user)
            
            return True, user.watts, self._get_unlocked_avatars(user), \
                f"Avatar '{avatar_id}' purchased for {price} watts"
                
        except Exception as e:
            return False, user.watts, self._get_unlocked_avatars(user), f"Purchase failed: {str(e)}"
    
    async def unlock_avatar_by_level(
        self,
        db: AsyncSession,
        user: User,
        avatar_id: str
    ) -> Tuple[bool, List[str], str]:
        """
        Unlock an avatar by level (free unlock).
        
        Level validation is done on the client side (client knows the config).
        Server just records the unlock.
        
        Args:
            db: Database session
            user: User unlocking the avatar
            avatar_id: ID of the avatar to unlock
            
        Returns:
            Tuple of (success, unlocked_avatars, message)
        """
        try:
            if not avatar_id:
                return False, self._get_unlocked_avatars(user), "Avatar ID is required"
            
            if self._is_avatar_unlocked(user, avatar_id):
                return False, self._get_unlocked_avatars(user), f"Avatar '{avatar_id}' is already unlocked"
            
            # Add avatar to unlocked list (no cost)
            unlocked = self._get_unlocked_avatars(user)
            unlocked.append(avatar_id)
            self._set_unlocked_avatars(user, unlocked)
            
            await db.flush()
            await db.refresh(user)
            
            return True, self._get_unlocked_avatars(user), \
                f"Avatar '{avatar_id}' unlocked by level"
                
        except Exception as e:
            return False, self._get_unlocked_avatars(user), f"Unlock failed: {str(e)}"
    
    def get_unlocked_avatars(self, user: User) -> List[str]:
        """Get list of unlocked avatar IDs for a user."""
        return self._get_unlocked_avatars(user)
    
    def get_current_avatar(self, user: User) -> str:
        """Get current equipped avatar ID."""
        return user.current_avatar or "telegram_avatar"


# Singleton instance
avatar_service = AvatarService()
