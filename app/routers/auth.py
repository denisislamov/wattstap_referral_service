"""
Authentication API endpoints.
"""

from datetime import datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.auth import (
    AuthResponse,
    PlayerInfo,
    ReferralResult,
    TelegramAuthRequest,
)
from app.services.telegram_auth import telegram_auth_service
from app.services.user_service import user_service
from app.services.referral_service import referral_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


def create_jwt_token(user_id: int, telegram_id: int) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: Internal user ID
        telegram_id: Telegram user ID
        
    Returns:
        JWT token string
    """
    now = datetime.utcnow()
    payload = {
        "sub": str(user_id),
        "telegram_id": telegram_id,
        "iat": now,
        "exp": now + timedelta(seconds=settings.jwt_expiration_seconds),
        "type": "access"
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@router.post(
    "/telegram",
    response_model=AuthResponse,
    summary="Authenticate via Telegram WebApp",
    description="""
    Authenticate a user using Telegram WebApp initData.
    
    If this is a new user and a referral code is provided (either directly or via start_param in initData):
    - The referral is applied
    - A friendship is created between the referrer and new user
    - The referrer receives a bonus
    
    Returns a JWT token and player information.
    """
)
async def authenticate_telegram(
    request: TelegramAuthRequest,
    db: AsyncSession = Depends(get_db)
) -> AuthResponse:
    """
    Authenticate user via Telegram WebApp initData.
    
    Flow:
    1. Validate initData signature
    2. Parse user information
    3. Find or create user
    4. Apply referral code if applicable
    5. Generate JWT token
    6. Return auth response
    """
    
    # 1. Validate and parse initData
    parsed_data, error = telegram_auth_service.validate_and_parse(request.init_data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {error}"
        )
    
    telegram_user = parsed_data.user
    
    # 2. Determine referral code (explicit parameter takes priority over start_param)
    referral_code = request.referral_code or parsed_data.start_param
    
    # 3. Find existing user or create new one
    user = await user_service.get_by_telegram_id(db, telegram_user.id)
    is_new_player = user is None
    referral_result = None
    
    if is_new_player:
        # --- NEW USER FLOW ---
        
        # Check referral code before creating user
        referrer = None
        if referral_code:
            referrer = await user_service.get_by_referral_code(db, referral_code)
            
            if referrer:
                # Validate referral can be applied
                can_apply, reason = await referral_service.can_apply_referral(
                    db, telegram_user.id, referrer
                )
                if not can_apply:
                    # Invalid referral, but continue with registration
                    referrer = None
                    referral_result = ReferralResult(
                        applied=False,
                        message=reason
                    )
        
        # Create new user
        user = await user_service.create_user(db, telegram_user)
        
        # Apply referral if we have a valid referrer
        if referrer:
            referral_result = await referral_service.apply_referral(db, user, referrer)
        elif referral_code and not referral_result:
            # Referral code was provided but referrer not found
            referral_result = ReferralResult(
                applied=False,
                message="Invalid referral code"
            )
        else:
            # No referral code provided
            referral_result = ReferralResult(
                applied=False,
                message="No referral code provided"
            )
    
    else:
        # --- EXISTING USER FLOW ---
        
        # Update last login
        await user_service.update_last_login(db, user)
        
        # Referral codes can only be applied on first login
        if referral_code:
            referral_result = ReferralResult(
                applied=False,
                message="Referral code can only be applied on first login"
            )
    
    # 4. Create JWT token
    token = create_jwt_token(user.id, user.telegram_id)
    
    # 5. Build response
    return AuthResponse(
        token=token,
        expires_in=settings.jwt_expiration_seconds,
        player=PlayerInfo(
            player_id=str(user.id),
            nickname=user.display_name,
            level=user.level,
            is_new_player=is_new_player,
            referral_code=user.referral_code
        ),
        referral=referral_result
    )


