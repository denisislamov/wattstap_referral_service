"""
Tests for authentication endpoints.
"""

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode, quote

import pytest
from httpx import AsyncClient

from app.config import settings


def create_mock_init_data(
    user_id: int = 123456789,
    username: str = "testuser",
    first_name: str = "Test",
    start_param: str = None,
    bot_token: str = None
) -> str:
    """
    Create a valid mock Telegram initData for testing.
    
    Args:
        user_id: Telegram user ID
        username: Telegram username
        first_name: User's first name
        start_param: Referral code from deep link
        bot_token: Bot token for signing (uses settings if not provided)
        
    Returns:
        Valid initData string
    """
    if bot_token is None:
        bot_token = settings.telegram_bot_token
    
    # Build user object
    user_data = {
        "id": user_id,
        "first_name": first_name,
        "username": username,
        "language_code": "en",
        "is_premium": False
    }
    
    # Build data dictionary
    data = {
        "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
        "user": json.dumps(user_data),
        "auth_date": str(int(time.time())),
    }
    
    if start_param:
        data["start_param"] = start_param
    
    # Sort keys and build data check string
    data_check_arr = []
    for key in sorted(data.keys()):
        data_check_arr.append(f"{key}={data[key]}")
    data_check_string = "\n".join(data_check_arr)
    
    # Compute hash
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode("utf-8"),
        hashlib.sha256
    ).digest()
    
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    data["hash"] = computed_hash
    
    # Build query string
    return urlencode(data)


class TestAuthEndpoints:
    """Tests for /auth/* endpoints."""
    
    @pytest.mark.asyncio
    async def test_authenticate_new_user(self, client: AsyncClient):
        """Test authenticating a new user."""
        init_data = create_mock_init_data(
            user_id=111111111,
            username="newuser",
            first_name="New"
        )
        
        response = await client.post(
            "/auth/telegram",
            json={"initData": init_data}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["token"]
        assert data["expiresIn"] == settings.jwt_expiration_seconds
        assert data["player"]["isNewPlayer"] is True
        assert data["player"]["nickname"] == "newuser"
        assert data["player"]["level"] == 1
        assert data["player"]["referralCode"]
    
    @pytest.mark.asyncio
    async def test_authenticate_existing_user(self, client: AsyncClient):
        """Test authenticating an existing user."""
        # First login (create user)
        init_data = create_mock_init_data(
            user_id=222222222,
            username="existinguser"
        )
        
        response1 = await client.post(
            "/auth/telegram",
            json={"initData": init_data}
        )
        assert response1.status_code == 200
        assert response1.json()["player"]["isNewPlayer"] is True
        
        # Second login (existing user)
        response2 = await client.post(
            "/auth/telegram",
            json={"initData": init_data}
        )
        assert response2.status_code == 200
        assert response2.json()["player"]["isNewPlayer"] is False
    
    @pytest.mark.asyncio
    async def test_authenticate_with_referral_code(self, client: AsyncClient):
        """Test authenticating a new user with a referral code."""
        # Create referrer user
        referrer_init_data = create_mock_init_data(
            user_id=333333333,
            username="referrer"
        )
        referrer_response = await client.post(
            "/auth/telegram",
            json={"initData": referrer_init_data}
        )
        referrer_code = referrer_response.json()["player"]["referralCode"]
        
        # Create new user with referral code
        new_user_init_data = create_mock_init_data(
            user_id=444444444,
            username="referred",
            start_param=f"REF_{referrer_code}"
        )
        
        response = await client.post(
            "/auth/telegram",
            json={"initData": new_user_init_data}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["player"]["isNewPlayer"] is True
        assert data["referral"]["applied"] is True
        assert data["referral"]["referrer"]["nickname"] == "referrer"
        assert data["referral"]["bonusForReferrer"] == settings.referral_bonus_watts
    
    @pytest.mark.asyncio
    async def test_cannot_use_own_referral_code(self, client: AsyncClient):
        """Test that user cannot use their own referral code."""
        # Create user
        init_data = create_mock_init_data(
            user_id=555555555,
            username="selfref"
        )
        
        # First, create the user without referral
        response1 = await client.post(
            "/auth/telegram",
            json={"initData": init_data}
        )
        own_code = response1.json()["player"]["referralCode"]
        
        # Try to authenticate with own code (as a new user - different ID)
        init_data_with_ref = create_mock_init_data(
            user_id=555555555,  # Same user
            username="selfref",
            start_param=f"REF_{own_code}"
        )
        
        response2 = await client.post(
            "/auth/telegram",
            json={"initData": init_data_with_ref}
        )
        
        # Should succeed but referral not applied
        assert response2.status_code == 200
        # Existing user - referral cannot be applied anyway
    
    @pytest.mark.asyncio
    async def test_invalid_init_data(self, client: AsyncClient):
        """Test authentication with invalid initData."""
        response = await client.post(
            "/auth/telegram",
            json={"initData": "invalid_data"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_referral_only_for_new_users(self, client: AsyncClient):
        """Test that referral code only works for new users."""
        # Create referrer
        referrer_init_data = create_mock_init_data(
            user_id=666666666,
            username="referrer2"
        )
        referrer_response = await client.post(
            "/auth/telegram",
            json={"initData": referrer_init_data}
        )
        referrer_code = referrer_response.json()["player"]["referralCode"]
        
        # Create existing user
        existing_init_data = create_mock_init_data(
            user_id=777777777,
            username="existing"
        )
        await client.post(
            "/auth/telegram",
            json={"initData": existing_init_data}
        )
        
        # Try to use referral code as existing user
        existing_with_ref = create_mock_init_data(
            user_id=777777777,
            username="existing",
            start_param=f"REF_{referrer_code}"
        )
        
        response = await client.post(
            "/auth/telegram",
            json={"initData": existing_with_ref}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["referral"]["applied"] is False
        assert "first login" in data["referral"]["message"].lower()


