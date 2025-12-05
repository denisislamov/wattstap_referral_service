"""
Telegram WebApp authentication service.

Handles validation of initData from Telegram WebApp and parsing user information.
"""

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple
from urllib.parse import parse_qs, unquote

from app.config import settings


@dataclass
class TelegramUser:
    """
    User data extracted from Telegram initData.
    
    Attributes:
        id: Telegram user ID
        first_name: User's first name
        last_name: User's last name (optional)
        username: Telegram username (optional)
        language_code: User's language code
        is_premium: Whether user has Telegram Premium
        photo_url: URL to user's profile photo (optional)
    """
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: str = "en"
    is_premium: bool = False
    photo_url: Optional[str] = None


@dataclass
class ParsedInitData:
    """
    Parsed data from Telegram WebApp initData.
    
    Attributes:
        user: Telegram user information
        auth_date: When the authentication happened
        hash: Hash for validation
        start_param: Start parameter from deep link (referral code)
        query_id: Query ID for inline mode
    """
    user: TelegramUser
    auth_date: datetime
    hash: str
    start_param: Optional[str] = None
    query_id: Optional[str] = None


class TelegramAuthService:
    """
    Service for validating Telegram WebApp authentication.
    
    Uses HMAC-SHA256 to verify that initData was signed by Telegram.
    """
    
    def __init__(self, bot_token: str):
        """
        Initialize the service.
        
        Args:
            bot_token: Telegram bot token for validation
        """
        self.bot_token = bot_token
        self._secret_key = self._compute_secret_key()
    
    def _compute_secret_key(self) -> bytes:
        """
        Compute the secret key for HMAC validation.
        
        The secret key is HMAC-SHA256 of bot token with "WebAppData" as key.
        
        Returns:
            Secret key bytes
        """
        return hmac.new(
            b"WebAppData",
            self.bot_token.encode("utf-8"),
            hashlib.sha256
        ).digest()
    
    def validate_init_data(
        self, 
        init_data: str, 
        max_age_seconds: int = 86400
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate initData from Telegram WebApp.
        
        Checks:
        1. Hash is present
        2. Hash matches computed hash
        3. auth_date is within max_age_seconds
        
        Args:
            init_data: Raw initData string from Telegram
            max_age_seconds: Maximum age of initData in seconds (default 24h)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Parse query string
            parsed = parse_qs(init_data, keep_blank_values=True)
            
            # Extract and verify hash
            received_hash = parsed.get("hash", [None])[0]
            if not received_hash:
                return False, "Missing hash in initData"
            
            # Build data check string (all params except hash, sorted alphabetically)
            data_check_arr = []
            for key in sorted(parsed.keys()):
                if key != "hash":
                    value = parsed[key][0]
                    data_check_arr.append(f"{key}={value}")
            
            data_check_string = "\n".join(data_check_arr)
            
            # Compute expected hash
            computed_hash = hmac.new(
                self._secret_key,
                data_check_string.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            
            # Compare hashes (timing-safe)
            if not hmac.compare_digest(computed_hash, received_hash):
                return False, "Invalid hash - data may have been tampered with"
            
            # Verify auth_date is not too old
            auth_date_str = parsed.get("auth_date", [None])[0]
            if auth_date_str:
                try:
                    auth_date = datetime.fromtimestamp(int(auth_date_str))
                    age = datetime.now() - auth_date
                    if age > timedelta(seconds=max_age_seconds):
                        return False, f"initData expired (age: {age.total_seconds()}s, max: {max_age_seconds}s)"
                except (ValueError, TypeError):
                    return False, "Invalid auth_date format"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def parse_init_data(self, init_data: str) -> Optional[ParsedInitData]:
        """
        Parse initData and extract user information.
        
        Args:
            init_data: Raw initData string from Telegram
            
        Returns:
            ParsedInitData object or None if parsing fails
        """
        try:
            parsed = parse_qs(init_data, keep_blank_values=True)
            
            # Parse user JSON
            user_json = parsed.get("user", [None])[0]
            if not user_json:
                return None
            
            # Decode URL-encoded JSON and parse
            user_data = json.loads(unquote(user_json))
            
            # Create TelegramUser object
            user = TelegramUser(
                id=user_data["id"],
                first_name=user_data.get("first_name", "User"),
                last_name=user_data.get("last_name"),
                username=user_data.get("username"),
                language_code=user_data.get("language_code", "en"),
                is_premium=user_data.get("is_premium", False),
                photo_url=user_data.get("photo_url")
            )
            
            # Parse auth_date
            auth_date_str = parsed.get("auth_date", ["0"])[0]
            auth_date = datetime.fromtimestamp(int(auth_date_str))
            
            # Get start_param (referral code from deep link)
            start_param = parsed.get("start_param", [None])[0]
            
            return ParsedInitData(
                user=user,
                auth_date=auth_date,
                hash=parsed.get("hash", [""])[0],
                start_param=start_param,
                query_id=parsed.get("query_id", [None])[0]
            )
            
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            print(f"Error parsing initData: {e}")
            return None
    
    def validate_and_parse(
        self, 
        init_data: str,
        max_age_seconds: int = 86400
    ) -> Tuple[Optional[ParsedInitData], Optional[str]]:
        """
        Validate and parse initData in one call.
        
        Args:
            init_data: Raw initData string from Telegram
            max_age_seconds: Maximum age of initData in seconds
            
        Returns:
            Tuple of (ParsedInitData or None, error_message or None)
        """
        # First validate
        is_valid, error = self.validate_init_data(init_data, max_age_seconds)
        if not is_valid:
            return None, error
        
        # Then parse
        parsed = self.parse_init_data(init_data)
        if not parsed:
            return None, "Failed to parse user data from initData"
        
        return parsed, None


# Singleton instance
telegram_auth_service = TelegramAuthService(settings.telegram_bot_token)


