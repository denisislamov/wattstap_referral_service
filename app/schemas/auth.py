"""
Authentication related schemas.
"""

from typing import Optional

from pydantic import BaseModel, Field


class TelegramAuthRequest(BaseModel):
    """Request body for Telegram authentication."""
    
    init_data: str = Field(
        ...,
        alias="initData",
        description="Raw initData string from Telegram WebApp",
        min_length=1
    )
    referral_code: Optional[str] = Field(
        None,
        alias="referralCode",
        description="Optional referral code from invite link",
        max_length=16
    )
    
    model_config = {
        "populate_by_name": True,
    }


class ReferrerInfo(BaseModel):
    """Information about the user who sent the referral."""
    
    user_id: int = Field(..., alias="userId", description="Referrer's Telegram ID")
    nickname: str = Field(..., description="Referrer's display name")
    avatar_url: Optional[str] = Field(None, alias="avatarUrl", description="Referrer's avatar URL")
    level: int = Field(..., description="Referrer's game level")
    
    model_config = {
        "populate_by_name": True,
    }


class ReferralResult(BaseModel):
    """Result of referral code application."""
    
    applied: bool = Field(False, description="Whether the referral was applied")
    referrer: Optional[ReferrerInfo] = Field(None, description="Info about who referred this user")
    bonus_for_referrer: int = Field(
        0,
        alias="bonusForReferrer",
        description="Bonus watts given to the referrer"
    )
    message: Optional[str] = Field(None, description="Status message")
    
    model_config = {
        "populate_by_name": True,
    }


class PlayerInfo(BaseModel):
    """Basic player information returned after authentication."""
    
    player_id: str = Field(..., alias="playerId", description="Player's internal ID")
    nickname: str = Field(..., description="Player's display name")
    level: int = Field(..., description="Player's current level")
    is_new_player: bool = Field(..., alias="isNewPlayer", description="Whether this is a new player")
    referral_code: str = Field(..., alias="referralCode", description="Player's own referral code")
    
    model_config = {
        "populate_by_name": True,
    }


class AuthResponse(BaseModel):
    """Response body for successful authentication."""
    
    token: str = Field(..., description="JWT access token")
    expires_in: int = Field(..., alias="expiresIn", description="Token expiration time in seconds")
    player: PlayerInfo = Field(..., description="Player information")
    referral: Optional[ReferralResult] = Field(None, description="Referral application result")
    
    model_config = {
        "populate_by_name": True,
    }



