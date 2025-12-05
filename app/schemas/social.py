"""
Social features related schemas.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FriendInfo(BaseModel):
    """Information about a friend."""
    
    player_id: str = Field(..., alias="playerId", description="Friend's internal ID")
    nickname: str = Field(..., description="Friend's display name")
    level: int = Field(..., description="Friend's current level")
    avatar_url: Optional[str] = Field(None, alias="avatarUrl", description="Friend's avatar URL")
    total_earnings: int = Field(
        0,
        alias="totalEarnings",
        description="Friend's total watts earned"
    )
    your_bonus: int = Field(
        0,
        alias="yourBonus",
        description="Bonus you earned from this friend"
    )
    invited_at: datetime = Field(..., alias="invitedAt", description="When this friend was added")
    
    model_config = {
        "populate_by_name": True,
    }


class FriendsListResponse(BaseModel):
    """Response containing list of friends."""
    
    friends: list[FriendInfo] = Field(default_factory=list, description="List of friends")
    total_friends: int = Field(0, alias="totalFriends", description="Total number of friends")
    total_bonus_earned: int = Field(
        0,
        alias="totalBonusEarned",
        description="Total bonus earned from all friends"
    )
    
    model_config = {
        "populate_by_name": True,
    }


class MyReferralResponse(BaseModel):
    """Response containing user's referral information."""
    
    referral_code: str = Field(..., alias="referralCode", description="User's referral code")
    invite_link: str = Field(..., alias="inviteLink", description="Full invite link for sharing")
    bonus_per_friend: int = Field(
        ...,
        alias="bonusPerFriend",
        description="Watts bonus for each invited friend"
    )
    total_friends_invited: int = Field(
        0,
        alias="totalFriendsInvited",
        description="Number of friends invited via referral"
    )
    total_bonus_earned: int = Field(
        0,
        alias="totalBonusEarned",
        description="Total bonus earned from referrals"
    )
    
    model_config = {
        "populate_by_name": True,
    }



