"""
Avatar purchase related schemas.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class PurchaseAvatarRequest(BaseModel):
    """Request to purchase an avatar."""
    
    avatar_id: str = Field(..., alias="avatarId", description="ID of the avatar to purchase")
    price: int = Field(..., ge=0, description="Expected price of the avatar (for validation)")
    currency: str = Field("watts", description="Currency to use: 'watts'")
    
    model_config = {
        "populate_by_name": True,
    }


class PurchaseAvatarResponse(BaseModel):
    """Response after avatar purchase attempt."""
    
    success: bool = Field(..., description="Whether the purchase was successful")
    avatar_id: str = Field(..., alias="avatarId", description="ID of the purchased avatar")
    new_watts_balance: int = Field(..., alias="newWattsBalance", description="Updated watts balance after purchase")
    unlocked_avatars: List[str] = Field(..., alias="unlockedAvatars", description="Full list of unlocked avatar IDs")
    message: str = Field("", description="Status message")
    
    model_config = {
        "populate_by_name": True,
    }


class UnlockAvatarByLevelRequest(BaseModel):
    """Request to unlock an avatar by level."""
    
    avatar_id: str = Field(..., alias="avatarId", description="ID of the avatar to unlock")
    
    model_config = {
        "populate_by_name": True,
    }


class UnlockAvatarByLevelResponse(BaseModel):
    """Response after level-based avatar unlock."""
    
    success: bool = Field(..., description="Whether the unlock was successful")
    avatar_id: str = Field(..., alias="avatarId", description="ID of the unlocked avatar")
    unlocked_avatars: List[str] = Field(..., alias="unlockedAvatars", description="Full list of unlocked avatar IDs")
    message: str = Field("", description="Status message")
    
    model_config = {
        "populate_by_name": True,
    }


class GetAvatarsResponse(BaseModel):
    """Response with player's avatar data."""
    
    success: bool = Field(..., description="Whether the request was successful")
    unlocked_avatars: List[str] = Field(..., alias="unlockedAvatars", description="List of unlocked avatar IDs")
    current_avatar: str = Field(..., alias="currentAvatar", description="Currently equipped avatar ID")
    
    model_config = {
        "populate_by_name": True,
    }
