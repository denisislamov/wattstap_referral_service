"""
User model for storing player data.
"""

import secrets
import string
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.friendship import Friendship


class User(Base):
    """
    User model representing a player in the game.
    
    Attributes:
        id: Primary key
        telegram_id: Unique Telegram user ID
        username: Telegram username (optional)
        first_name: User's first name
        last_name: User's last name (optional)
        photo_url: URL to user's profile photo
        language_code: User's language code
        is_premium: Whether user has Telegram Premium
        
        level: Current player level
        watts: Current watts (in-game currency)
        
        referral_code: Unique code for inviting others
        referred_by_id: ID of user who invited this user
        
        created_at: When user was created
        updated_at: When user was last updated
        last_login_at: When user last logged in
    """
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # Telegram data
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, 
        unique=True, 
        nullable=False, 
        index=True
    )
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False, default="User")
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    language_code: Mapped[str] = mapped_column(String(10), default="en")
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Game data
    level: Mapped[int] = mapped_column(BigInteger, default=1)
    watts: Mapped[int] = mapped_column(BigInteger, default=0)
    
    # Referral system
    referral_code: Mapped[str] = mapped_column(
        String(16), 
        unique=True, 
        nullable=False, 
        index=True
    )
    referred_by_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, 
        ForeignKey("users.id"), 
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True
    )
    last_login_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    referred_by: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side=[id],
        back_populates="referrals",
        foreign_keys=[referred_by_id]
    )
    
    referrals: Mapped[list["User"]] = relationship(
        "User",
        back_populates="referred_by",
        foreign_keys=[referred_by_id]
    )
    
    # Friendships (user initiated)
    friendships: Mapped[list["Friendship"]] = relationship(
        "Friendship",
        back_populates="user",
        foreign_keys="Friendship.user_id",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"
    
    @property
    def display_name(self) -> str:
        """Returns the best available display name."""
        if self.username:
            return self.username
        if self.first_name:
            return self.first_name
        return f"User_{self.telegram_id}"
    
    @staticmethod
    def generate_referral_code(length: int = 8) -> str:
        """
        Generate a unique referral code.
        
        Args:
            length: Length of the code (default 8)
            
        Returns:
            Generated referral code
        """
        # Use uppercase letters and digits, excluding similar-looking characters
        alphabet = string.ascii_uppercase + string.digits
        # Remove confusing characters: 0, O, I, L, 1
        alphabet = alphabet.replace('0', '').replace('O', '').replace('I', '').replace('L', '').replace('1', '')
        return ''.join(secrets.choice(alphabet) for _ in range(length))



