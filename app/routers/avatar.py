"""
Avatar API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.avatar import (
    PurchaseAvatarRequest,
    PurchaseAvatarResponse,
    UnlockAvatarByLevelRequest,
    UnlockAvatarByLevelResponse,
    GetAvatarsResponse,
)
from app.services.avatar_service import avatar_service

router = APIRouter(prefix="/avatars", tags=["Avatars"])


@router.get(
    "",
    response_model=GetAvatarsResponse,
    summary="Get player avatars",
    description="Get the player's unlocked avatars and current equipped avatar."
)
async def get_avatars(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> GetAvatarsResponse:
    """Get player's avatar data."""
    return GetAvatarsResponse(
        success=True,
        unlockedAvatars=avatar_service.get_unlocked_avatars(current_user),
        currentAvatar=avatar_service.get_current_avatar(current_user)
    )


@router.post(
    "/purchase",
    response_model=PurchaseAvatarResponse,
    summary="Purchase an avatar",
    description="""
    Purchase an avatar using in-game currency (watts).
    
    The server validates:
    - Avatar is not already unlocked
    - Player has enough currency
    - Deducts the cost from player's balance
    
    Returns updated watts balance and unlocked avatars list.
    """
)
async def purchase_avatar(
    request: PurchaseAvatarRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PurchaseAvatarResponse:
    """Purchase an avatar with watts."""
    success, new_balance, unlocked, message = await avatar_service.purchase_avatar(
        db=db,
        user=current_user,
        avatar_id=request.avatar_id,
        price=request.price,
        currency=request.currency
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return PurchaseAvatarResponse(
        success=True,
        avatarId=request.avatar_id,
        newWattsBalance=new_balance,
        unlockedAvatars=unlocked,
        message=message
    )


@router.post(
    "/unlock-by-level",
    response_model=UnlockAvatarByLevelResponse,
    summary="Unlock avatar by level",
    description="""
    Unlock an avatar that requires a certain level (free unlock).
    
    The client validates level requirements locally from config.
    The server records the unlock.
    """
)
async def unlock_avatar_by_level(
    request: UnlockAvatarByLevelRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UnlockAvatarByLevelResponse:
    """Unlock an avatar by reaching the required level."""
    success, unlocked, message = await avatar_service.unlock_avatar_by_level(
        db=db,
        user=current_user,
        avatar_id=request.avatar_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return UnlockAvatarByLevelResponse(
        success=True,
        avatarId=request.avatar_id,
        unlockedAvatars=unlocked,
        message=message
    )
