"""
Pydantic schemas for Mining Balance configuration API.

Field names use camelCase to match Unity client's JsonUtility expectations.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Daily Progression
# ──────────────────────────────────────────────

class DailyProgressionItem(BaseModel):
    """Single day progression data — mirrors Unity DailyProgressionData."""
    
    day: int = Field(..., description="Day number (1-30)")
    playtimeSec: int = Field(900, description="Playtime in seconds per session")
    tapsPerSession: int = Field(1950, description="Taps per session")
    tapsPerDay: int = Field(3900, description="Taps per day")
    expPerDay: int = Field(3900, description="Experience earned per day")
    coinsFromTaps: float = Field(3946.8, description="Coins earned from taps")
    coinsFromOfflineBonus: float = Field(3000.0, description="Coins from offline bonus")
    profitCoins: float = Field(6946.8, description="Total profit coins per day")
    cumulativeProfitCoins: float = Field(6946.8, description="Cumulative profit coins up to this day")
    cumulativeExp: int = Field(3900, description="Cumulative experience up to this day")
    
    model_config = {"populate_by_name": True}


class DailyProgressionCreate(BaseModel):
    """Schema for creating/updating a daily progression entry (admin)."""
    
    day: int = Field(..., ge=1, le=30)
    playtimeSec: int = Field(900, ge=0)
    tapsPerSession: int = Field(1950, ge=0)
    tapsPerDay: int = Field(3900, ge=0)
    expPerDay: int = Field(3900, ge=0)
    coinsFromTaps: float = Field(3946.8, ge=0)
    coinsFromOfflineBonus: float = Field(3000.0, ge=0)
    profitCoins: float = Field(6946.8, ge=0)
    cumulativeProfitCoins: float = Field(6946.8, ge=0)
    cumulativeExp: int = Field(3900, ge=0)


# ──────────────────────────────────────────────
# Mining Balance (full config)
# ──────────────────────────────────────────────

class MiningBalanceResponse(BaseModel):
    """
    Full mining balance config — mirrors Unity MiningBalanceConfig.
    
    This is what the Unity client receives and applies at runtime.
    Field names match the Unity class fields exactly (camelCase).
    """
    
    # Start Parameters
    coinsPerTap: int = Field(1, description="Coins earned per tap")
    expPerTap: int = Field(1, description="Experience earned per tap")
    energyCostPerTap: int = Field(0, description="Energy cost per tap")
    startCapacityHits: int = Field(1500, description="Initial hit capacity")
    cooldownPerHitSec: float = Field(2.0, description="Cooldown per hit in seconds")
    critMultiplier: float = Field(1.2, description="Critical hit damage multiplier")
    chanceCritPercent: float = Field(1.0, description="Critical hit chance in percent")
    avgPlaytimeMinutes: int = Field(15, description="Average playtime in minutes")
    tapsPerSecond: int = Field(10, description="Taps per second")
    profitPerHour: int = Field(500, description="Profit per hour (passive income)")
    maxHoursOffline: int = Field(3, description="Max offline income hours")
    sessionsPerDay: int = Field(2, description="Sessions per day")
    
    # Daily Progression
    dailyProgression: List[DailyProgressionItem] = Field(
        default_factory=list,
        description="30-day progression data"
    )
    
    model_config = {"populate_by_name": True}


class MiningBalancePublicResponse(BaseModel):
    """Public API response wrapping the mining balance config."""
    
    success: bool = True
    balance: MiningBalanceResponse


# ──────────────────────────────────────────────
# Admin schemas
# ──────────────────────────────────────────────

class MiningBalanceAdminResponse(BaseModel):
    """Admin response with additional metadata."""
    
    success: bool = True
    version: str = "default"
    isActive: bool = True
    balance: MiningBalanceResponse
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class MiningBalanceUpdateRequest(BaseModel):
    """Admin request to update balance parameters."""
    
    coinsPerTap: Optional[int] = None
    expPerTap: Optional[int] = None
    energyCostPerTap: Optional[int] = None
    startCapacityHits: Optional[int] = None
    cooldownPerHitSec: Optional[float] = None
    critMultiplier: Optional[float] = None
    chanceCritPercent: Optional[float] = None
    avgPlaytimeMinutes: Optional[int] = None
    tapsPerSecond: Optional[int] = None
    profitPerHour: Optional[int] = None
    maxHoursOffline: Optional[int] = None
    sessionsPerDay: Optional[int] = None
    
    dailyProgression: Optional[List[DailyProgressionCreate]] = None


class MiningBalanceSeedResponse(BaseModel):
    """Response after seeding balance from CSV."""
    
    success: bool = True
    message: str = ""
    version: str = "default"
    paramsCount: int = 0
    daysCount: int = 0
