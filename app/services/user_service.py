"""
User service for managing user data.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.telegram_auth import TelegramUser
from app.config import settings


class UserService:
    """
    Service for user management operations.
    
    Handles creating, finding, and updating users.
    """
    
    async def get_by_telegram_id(
        self, 
        db: AsyncSession, 
        telegram_id: int
    ) -> Optional[User]:
        """
        Find a user by their Telegram ID.
        
        Args:
            db: Database session
            telegram_id: Telegram user ID
            
        Returns:
            User object or None if not found
        """
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Optional[User]:
        """
        Find a user by their internal ID.
        
        Args:
            db: Database session
            user_id: Internal user ID
            
        Returns:
            User object or None if not found
        """
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_referral_code(
        self, 
        db: AsyncSession, 
        referral_code: str
    ) -> Optional[User]:
        """
        Find a user by their referral code.
        
        Args:
            db: Database session
            referral_code: Referral code (with or without REF_ prefix)
            
        Returns:
            User object or None if not found
        """
        # Clean the code (remove REF_ prefix if present)
        clean_code = referral_code.replace("REF_", "").upper()
        
        result = await db.execute(
            select(User).where(User.referral_code == clean_code)
        )
        return result.scalar_one_or_none()
    
    async def create_user(
        self, 
        db: AsyncSession, 
        telegram_user: TelegramUser,
        initial_watts: int = 1000
    ) -> User:
        """
        Create a new user from Telegram data.
        
        Args:
            db: Database session
            telegram_user: Telegram user data
            initial_watts: Initial watts for new user
            
        Returns:
            Created User object
        """
        # Generate unique referral code
        referral_code = await self._generate_unique_referral_code(db)
        
        user = User(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            photo_url=telegram_user.photo_url,
            language_code=telegram_user.language_code,
            is_premium=telegram_user.is_premium,
            referral_code=referral_code,
            watts=initial_watts,
            level=1
        )
        
        db.add(user)
        await db.flush()  # Get the ID without committing
        await db.refresh(user)
        
        return user
    
    async def _generate_unique_referral_code(self, db: AsyncSession) -> str:
        """
        Generate a unique referral code.
        
        Keeps generating until a unique code is found.
        
        Args:
            db: Database session
            
        Returns:
            Unique referral code
        """
        max_attempts = 10
        for _ in range(max_attempts):
            code = User.generate_referral_code(settings.referral_code_length)
            
            # Check if code already exists
            existing = await db.execute(
                select(User.id).where(User.referral_code == code)
            )
            if not existing.scalar_one_or_none():
                return code
        
        # If we couldn't generate unique code, use longer one
        return User.generate_referral_code(settings.referral_code_length + 4)
    
    async def update_last_login(
        self, 
        db: AsyncSession, 
        user: User
    ) -> User:
        """
        Update user's last login timestamp.
        
        Args:
            db: Database session
            user: User to update
            
        Returns:
            Updated User object
        """
        user.last_login_at = datetime.utcnow()
        await db.flush()
        return user
    
    async def add_watts(
        self, 
        db: AsyncSession, 
        user: User, 
        amount: int
    ) -> User:
        """
        Add watts to user's balance.
        
        Args:
            db: Database session
            user: User to update
            amount: Amount of watts to add
            
        Returns:
            Updated User object
        """
        user.watts += amount
        await db.flush()
        return user


# Singleton instance
user_service = UserService()


