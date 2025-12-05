"""
Friendship model for storing friend relationships.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Friendship(Base):
    """
    Friendship model representing a one-way friend relationship.
    
    For mutual friendship, two records are created:
    - user_id -> friend_id
    - friend_id -> user_id
    
    Attributes:
        id: Primary key
        user_id: The user who has this friend
        friend_id: The friend
        source: How the friendship was created (referral, manual, etc.)
        created_at: When friendship was created
    """
    
    __tablename__ = "friendships"
    
    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # Friend relationship
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    friend_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Metadata
    source: Mapped[str] = mapped_column(
        String(50),
        default="referral",
        nullable=False
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="friendships"
    )
    
    friend: Mapped["User"] = relationship(
        "User",
        foreign_keys=[friend_id]
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "friend_id", name="uq_friendship_user_friend"),
    )
    
    def __repr__(self) -> str:
        return f"<Friendship(user_id={self.user_id}, friend_id={self.friend_id}, source={self.source})>"



