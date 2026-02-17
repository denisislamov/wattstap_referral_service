"""
Progress service for managing player progress data.
"""

from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.progress import PlayerProgress


class ProgressService:
    """
    Service for player progress management operations.
    
    Handles saving, loading, and resetting player progress.
    """
    
    # Default values for new players
    DEFAULT_LEVEL = 1
    DEFAULT_WATTS = 0
    DEFAULT_CURRENT_XP = 0
    DEFAULT_TOTAL_XP = 0
    
    def get_progress(self, user: User) -> PlayerProgress:
        """
        Get player progress from user model.
        
        Args:
            user: User model
            
        Returns:
            PlayerProgress object
        """
        return PlayerProgress(
            level=user.level,
            watts=user.watts,
            currentXp=user.current_xp,
            totalXp=user.total_xp
        )
    
    async def save_progress(
        self,
        db: AsyncSession,
        user: User,
        level: int,
        watts: int,
        current_xp: int,
        total_xp: int
    ) -> Tuple[bool, PlayerProgress, str]:
        """
        Save player progress to database.
        
        Args:
            db: Database session
            user: User to update
            level: New level
            watts: New watts balance
            current_xp: New current XP
            total_xp: New total XP
            
        Returns:
            Tuple of (success, progress, message)
        """
        try:
            # Validate data - only allow progress to increase (anti-cheat)
            # Level can only go up
            if level < user.level:
                level = user.level
            
            # Total XP can only increase
            if total_xp < user.total_xp:
                total_xp = user.total_xp
            
            # Watts can go up or down (spending)
            # No validation needed for watts
            
            # Update user
            user.level = level
            user.watts = watts
            user.current_xp = current_xp
            user.total_xp = total_xp
            
            await db.flush()
            await db.refresh(user)
            
            progress = self.get_progress(user)
            return True, progress, "Progress saved successfully"
            
        except Exception as e:
            return False, self.get_progress(user), f"Failed to save progress: {str(e)}"
    
    async def reset_progress(
        self,
        db: AsyncSession,
        user: User
    ) -> Tuple[bool, PlayerProgress, str]:
        """
        Reset player progress to default values.
        
        Args:
            db: Database session
            user: User to reset
            
        Returns:
            Tuple of (success, progress, message)
        """
        try:
            user.level = self.DEFAULT_LEVEL
            user.watts = self.DEFAULT_WATTS
            user.current_xp = self.DEFAULT_CURRENT_XP
            user.total_xp = self.DEFAULT_TOTAL_XP
            
            await db.flush()
            await db.refresh(user)
            
            progress = self.get_progress(user)
            return True, progress, "Progress reset successfully"
            
        except Exception as e:
            return False, self.get_progress(user), f"Failed to reset progress: {str(e)}"
    
    async def add_resources(
        self,
        db: AsyncSession,
        user: User,
        watts: int = 0,
        xp: int = 0
    ) -> Tuple[bool, "PlayerProgress", int, int, str]:
        """
        Add watts and/or XP to a player (debug operation).
        
        Properly updates both current_xp and total_xp.
        Watts and XP can only be added (non-negative).
        
        Args:
            db: Database session
            user: User to update
            watts: Amount of watts to add (>= 0)
            xp: Amount of XP to add (>= 0)
            
        Returns:
            Tuple of (success, progress, added_watts, added_xp, message)
        """
        try:
            if watts < 0 or xp < 0:
                return False, self.get_progress(user), 0, 0, "Cannot add negative amounts"
            
            if watts == 0 and xp == 0:
                return False, self.get_progress(user), 0, 0, "No resources to add (both watts and xp are 0)"
            
            # Add watts
            user.watts += watts
            
            # Add XP: update both current and total
            user.current_xp += xp
            user.total_xp += xp
            
            await db.flush()
            await db.refresh(user)
            
            progress = self.get_progress(user)
            
            parts = []
            if watts > 0:
                parts.append(f"+{watts} watts")
            if xp > 0:
                parts.append(f"+{xp} XP")
            message = f"Added {', '.join(parts)} to player"
            
            return True, progress, watts, xp, message
            
        except Exception as e:
            return False, self.get_progress(user), 0, 0, f"Failed to add resources: {str(e)}"
    
    def is_new_player(self, user: User) -> bool:
        """
        Check if user is a new player (no progress saved).
        
        Args:
            user: User to check
            
        Returns:
            True if new player
        """
        return (
            user.level == self.DEFAULT_LEVEL and
            user.watts == self.DEFAULT_WATTS and
            user.current_xp == self.DEFAULT_CURRENT_XP and
            user.total_xp == self.DEFAULT_TOTAL_XP
        )


# Singleton instance
progress_service = ProgressService()

