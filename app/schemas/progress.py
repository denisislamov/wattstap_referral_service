"""
Player progress related schemas.
"""

from typing import Optional
from pydantic import BaseModel, Field


class PlayerProgress(BaseModel):
    """Current player progress data."""
    
    level: int = Field(..., description="Current player level")
    watts: int = Field(..., description="Current watts balance")
    current_xp: int = Field(..., alias="currentXp", description="Current XP towards next level")
    total_xp: int = Field(..., alias="totalXp", description="Total XP earned")
    
    model_config = {
        "populate_by_name": True,
    }


class SaveProgressRequest(BaseModel):
    """Request to save player progress."""
    
    level: int = Field(..., ge=1, description="Current player level")
    watts: int = Field(..., ge=0, description="Current watts balance")
    current_xp: int = Field(..., alias="currentXp", ge=0, description="Current XP towards next level")
    total_xp: int = Field(..., alias="totalXp", ge=0, description="Total XP earned")
    
    model_config = {
        "populate_by_name": True,
    }


class SaveProgressResponse(BaseModel):
    """Response after saving progress."""
    
    success: bool = Field(..., description="Whether the save was successful")
    progress: PlayerProgress = Field(..., description="Saved progress data")
    message: Optional[str] = Field(None, description="Optional status message")
    
    model_config = {
        "populate_by_name": True,
    }


class LoadProgressResponse(BaseModel):
    """Response when loading player progress."""
    
    success: bool = Field(..., description="Whether loading was successful")
    progress: PlayerProgress = Field(..., description="Player progress data")
    is_new_player: bool = Field(..., alias="isNewPlayer", description="Whether this is a new player with no saved progress")
    
    model_config = {
        "populate_by_name": True,
    }


class ResetProgressRequest(BaseModel):
    """Request to reset player progress."""
    
    confirm: bool = Field(..., description="Must be true to confirm reset")
    
    model_config = {
        "populate_by_name": True,
    }


class ResetProgressResponse(BaseModel):
    """Response after resetting progress."""
    
    success: bool = Field(..., description="Whether the reset was successful")
    progress: PlayerProgress = Field(..., description="New progress data after reset")
    message: str = Field(..., description="Status message")
    
    model_config = {
        "populate_by_name": True,
    }


class AddResourcesRequest(BaseModel):
    """Request to add XP and/or watts to a player (debug)."""
    
    watts: int = Field(0, ge=0, description="Amount of watts to add")
    xp: int = Field(0, ge=0, description="Amount of XP to add")
    
    model_config = {
        "populate_by_name": True,
    }


class AddResourcesResponse(BaseModel):
    """Response after adding resources."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    progress: PlayerProgress = Field(..., description="Updated progress data")
    added_watts: int = Field(..., alias="addedWatts", description="Amount of watts actually added")
    added_xp: int = Field(..., alias="addedXp", description="Amount of XP actually added")
    message: str = Field(..., description="Status message")
    
    model_config = {
        "populate_by_name": True,
    }

