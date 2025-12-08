"""
Application configuration loaded from environment variables.
"""

import json
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = "WattsTap Referral Service"
    app_env: str = "development"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/wattstap_referral"
    database_echo: bool = False
    
    @field_validator("database_url", mode="before")
    @classmethod
    def convert_database_url(cls, v: str) -> str:
        """Convert postgres:// to postgresql+asyncpg:// for asyncpg compatibility."""
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    # Telegram
    telegram_bot_token: str = ""
    telegram_bot_username: str = "WattsTapDevTemp_bot"
    telegram_app_name: str = "play"
    
    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_seconds: int = 86400  # 24 hours
    
    # Referral System
    referral_bonus_watts: int = 5000
    referral_code_length: int = 8
    
    # CORS - stored as string, parsed via property
    cors_origins_str: str = "*"
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from string."""
        v = self.cors_origins_str
        # Try JSON first
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        # Fallback: comma-separated or single value
        if "," in v:
            return [origin.strip() for origin in v.split(",")]
        return [v]
    
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


# Global settings instance
settings = Settings()



