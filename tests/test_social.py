"""
Tests for social endpoints.
"""

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

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
    """Create a valid mock Telegram initData for testing."""
    if bot_token is None:
        bot_token = settings.telegram_bot_token
    
    user_data = {
        "id": user_id,
        "first_name": first_name,
        "username": username,
        "language_code": "en",
        "is_premium": False
    }
    
    data = {
        "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
        "user": json.dumps(user_data),
        "auth_date": str(int(time.time())),
    }
    
    if start_param:
        data["start_param"] = start_param
    
    data_check_arr = []
    for key in sorted(data.keys()):
        data_check_arr.append(f"{key}={data[key]}")
    data_check_string = "\n".join(data_check_arr)
    
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
    return urlencode(data)


async def create_authenticated_user(
    client: AsyncClient,
    user_id: int,
    username: str,
    referral_code: str = None
) -> tuple[str, str]:
    """
    Create and authenticate a user.
    
    Returns:
        Tuple of (jwt_token, referral_code)
    """
    init_data = create_mock_init_data(
        user_id=user_id,
        username=username,
        start_param=f"REF_{referral_code}" if referral_code else None
    )
    
    response = await client.post(
        "/auth/telegram",
        json={"initData": init_data}
    )
    
    data = response.json()
    return data["token"], data["player"]["referralCode"]


class TestSocialEndpoints:
    """Tests for /social/* endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_my_referral(self, client: AsyncClient):
        """Test getting own referral information."""
        token, referral_code = await create_authenticated_user(
            client, 888888888, "refuser"
        )
        
        response = await client.get(
            "/social/my-referral",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["referralCode"] == referral_code
        assert settings.telegram_bot_username in data["inviteLink"]
        assert f"REF_{referral_code}" in data["inviteLink"]
        assert data["bonusPerFriend"] == settings.referral_bonus_watts
        assert data["totalFriendsInvited"] == 0
        assert data["totalBonusEarned"] == 0
    
    @pytest.mark.asyncio
    async def test_get_my_referral_unauthorized(self, client: AsyncClient):
        """Test getting referral info without authentication."""
        response = await client.get("/social/my-referral")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_friends_empty(self, client: AsyncClient):
        """Test getting friends list when empty."""
        token, _ = await create_authenticated_user(
            client, 999999999, "lonelyuser"
        )
        
        response = await client.get(
            "/social/friends",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["friends"] == []
        assert data["totalFriends"] == 0
        assert data["totalBonusEarned"] == 0
    
    @pytest.mark.asyncio
    async def test_get_friends_with_referral(self, client: AsyncClient):
        """Test getting friends list after referral."""
        # Create referrer
        referrer_token, referrer_code = await create_authenticated_user(
            client, 100000001, "referrer"
        )
        
        # Create referred user
        _, _ = await create_authenticated_user(
            client, 100000002, "referred",
            referral_code=referrer_code
        )
        
        # Check referrer's friends
        response = await client.get(
            "/social/friends",
            headers={"Authorization": f"Bearer {referrer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["totalFriends"] == 1
        assert data["totalBonusEarned"] == settings.referral_bonus_watts
        assert len(data["friends"]) == 1
        assert data["friends"][0]["nickname"] == "referred"
        assert data["friends"][0]["yourBonus"] == settings.referral_bonus_watts
    
    @pytest.mark.asyncio
    async def test_referral_stats_update(self, client: AsyncClient):
        """Test that referral stats update correctly after invites."""
        # Create referrer
        referrer_token, referrer_code = await create_authenticated_user(
            client, 200000001, "bigref"
        )
        
        # Check initial stats
        response = await client.get(
            "/social/my-referral",
            headers={"Authorization": f"Bearer {referrer_token}"}
        )
        assert response.json()["totalFriendsInvited"] == 0
        
        # Invite 3 users
        for i in range(3):
            await create_authenticated_user(
                client, 200000002 + i, f"friend{i}",
                referral_code=referrer_code
            )
        
        # Check updated stats
        response = await client.get(
            "/social/my-referral",
            headers={"Authorization": f"Bearer {referrer_token}"}
        )
        data = response.json()
        
        assert data["totalFriendsInvited"] == 3
        assert data["totalBonusEarned"] == settings.referral_bonus_watts * 3
    
    @pytest.mark.asyncio
    async def test_mutual_friendship(self, client: AsyncClient):
        """Test that referral creates mutual friendship."""
        # Create referrer
        referrer_token, referrer_code = await create_authenticated_user(
            client, 300000001, "mutual1"
        )
        
        # Create referred user
        referred_token, _ = await create_authenticated_user(
            client, 300000002, "mutual2",
            referral_code=referrer_code
        )
        
        # Check referrer's friends
        response1 = await client.get(
            "/social/friends",
            headers={"Authorization": f"Bearer {referrer_token}"}
        )
        assert response1.json()["totalFriends"] == 1
        assert response1.json()["friends"][0]["nickname"] == "mutual2"
        
        # Check referred user's friends
        response2 = await client.get(
            "/social/friends",
            headers={"Authorization": f"Bearer {referred_token}"}
        )
        assert response2.json()["totalFriends"] == 1
        assert response2.json()["friends"][0]["nickname"] == "mutual1"
        # Referred user doesn't get bonus (only referrer does)
        assert response2.json()["friends"][0]["yourBonus"] == 0


