"""
Social features API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.social import (
    FriendInfo,
    FriendsListResponse,
    MyReferralResponse,
)
from app.services.referral_service import referral_service

router = APIRouter(prefix="/social", tags=["Social"])


@router.get(
    "/my-referral",
    response_model=MyReferralResponse,
    summary="Get your referral information",
    description="""
    Get your personal referral code and statistics.
    
    Returns:
    - Your referral code
    - Full invite link for sharing
    - Number of friends you've invited
    - Total bonus earned from referrals
    """
)
async def get_my_referral(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MyReferralResponse:
    """Get current user's referral information."""
    
    # Get referral statistics
    stats = await referral_service.get_referral_stats(db, current_user)
    
    # Build invite link
    invite_link = f"https://t.me/{settings.telegram_bot_username}?startattach=REF_{current_user.referral_code}"
    
    return MyReferralResponse(
        referral_code=current_user.referral_code,
        invite_link=invite_link,
        bonus_per_friend=stats["bonus_per_friend"],
        total_friends_invited=stats["total_friends_invited"],
        total_bonus_earned=stats["total_bonus_earned"]
    )


@router.get(
    "/friends",
    response_model=FriendsListResponse,
    summary="Get list of friends",
    description="""
    Get list of all your friends.
    
    Friends are added when:
    - Someone uses your referral code
    - You use someone's referral code
    
    Returns information about each friend including the bonus you earned from them.
    """
)
async def get_friends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FriendsListResponse:
    """Get current user's friends list."""
    
    # Get all friends
    friends_data = await referral_service.get_friends(db, current_user)
    
    friends_list = []
    total_bonus = 0
    
    for friend, friendship in friends_data:
        # Calculate bonus from this friend
        # We get bonus only if we referred them
        your_bonus = 0
        if friend.referred_by_id == current_user.id:
            your_bonus = referral_service.bonus_per_referral
            total_bonus += your_bonus
        
        friends_list.append(FriendInfo(
            player_id=str(friend.id),
            nickname=friend.display_name,
            level=friend.level,
            avatar_url=friend.photo_url,
            total_earnings=friend.watts,
            your_bonus=your_bonus,
            invited_at=friendship.created_at
        ))
    
    return FriendsListResponse(
        friends=friends_list,
        total_friends=len(friends_list),
        total_bonus_earned=total_bonus
    )


