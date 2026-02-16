"""
Mining balance configuration models.

Stores the game balance parameters and daily progression data,
mirroring the Unity MiningBalanceConfig structure.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, BigInteger, Float, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class MiningBalanceParams(Base):
    """
    Start parameters for mining balance.
    
    Corresponds to the 'Start Parameters' section of WattsBalanceMining.csv
    and MiningBalanceConfig fields in Unity.
    """
    __tablename__ = "mining_balance_params"

    id = Column(Integer, primary_key=True, index=True)
    
    # Version label (e.g. "v1", "default") to support multiple balance versions
    version = Column(String, nullable=False, default="default", unique=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Start Parameters (mirrors MiningBalanceConfig fields)
    coins_per_tap = Column(Integer, nullable=False, default=1)
    exp_per_tap = Column(Integer, nullable=False, default=1)
    energy_cost_per_tap = Column(Integer, nullable=False, default=0)
    start_capacity_hits = Column(Integer, nullable=False, default=1500)
    cooldown_per_hit_sec = Column(Float, nullable=False, default=2.0)
    crit_multiplier = Column(Float, nullable=False, default=1.2)
    chance_crit_percent = Column(Float, nullable=False, default=1.0)
    avg_playtime_minutes = Column(Integer, nullable=False, default=15)
    taps_per_second = Column(Integer, nullable=False, default=10)
    profit_per_hour = Column(Integer, nullable=False, default=500)
    max_hours_offline = Column(Integer, nullable=False, default=3)
    sessions_per_day = Column(Integer, nullable=False, default=2)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to daily progression
    daily_progression = relationship(
        "MiningBalanceDailyProgression",
        back_populates="balance_params",
        cascade="all, delete-orphan",
        order_by="MiningBalanceDailyProgression.day"
    )


class MiningBalanceDailyProgression(Base):
    """
    Daily progression data for mining balance.
    
    Corresponds to DailyProgressionData in Unity and 
    the daily progression rows in WattsBalanceMining.csv.
    """
    __tablename__ = "mining_balance_daily_progression"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to params
    balance_params_id = Column(Integer, ForeignKey("mining_balance_params.id", ondelete="CASCADE"), nullable=False)
    
    # Day number (1-30)
    day = Column(Integer, nullable=False)
    
    # Progression data
    playtime_sec = Column(Integer, nullable=False, default=900)
    taps_per_session = Column(Integer, nullable=False, default=1950)
    taps_per_day = Column(Integer, nullable=False, default=3900)
    exp_per_day = Column(BigInteger, nullable=False, default=3900)
    coins_from_taps = Column(Float, nullable=False, default=3946.8)
    coins_from_offline_bonus = Column(Float, nullable=False, default=3000.0)
    profit_coins = Column(Float, nullable=False, default=6946.8)
    cumulative_profit_coins = Column(Float, nullable=False, default=6946.8)
    cumulative_exp = Column(BigInteger, nullable=False, default=3900)
    
    # Relationship back to params
    balance_params = relationship("MiningBalanceParams", back_populates="daily_progression")
