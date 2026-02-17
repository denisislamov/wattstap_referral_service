"""
Development/testing endpoints.
Only available in non-production environments.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.friendship import Friendship
from app.schemas.progress import AddResourcesRequest, AddResourcesResponse
from app.services.progress_service import progress_service

router = APIRouter(prefix="/dev", tags=["Development"])


def check_dev_mode():
    """Dependency to ensure we're not in production."""
    if settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is not available in production"
        )


@router.delete(
    "/reset-all",
    summary="Reset all users and friendships",
    description="Deletes all users and friendships. FOR TESTING ONLY.",
    dependencies=[Depends(check_dev_mode)]
)
async def reset_all(db: AsyncSession = Depends(get_db)):
    """Delete all users and friendships for testing."""
    
    # Delete all friendships first (foreign key constraint)
    await db.execute(delete(Friendship))
    
    # Delete all users
    await db.execute(delete(User))
    
    await db.commit()
    
    return {"message": "All users and friendships deleted", "status": "ok"}


@router.delete(
    "/reset-user/{telegram_id}",
    summary="Delete a specific user",
    description="Deletes a user by Telegram ID and their friendships. FOR TESTING ONLY.",
    dependencies=[Depends(check_dev_mode)]
)
async def reset_user(
    telegram_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific user by Telegram ID."""
    
    from sqlalchemy import select, or_
    
    # Find user
    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with telegram_id {telegram_id} not found"
        )
    
    # Delete friendships where user is involved
    await db.execute(
        delete(Friendship).where(
            or_(
                Friendship.user_id == user.id,
                Friendship.friend_id == user.id
            )
        )
    )
    
    # Clear referred_by for users who were referred by this user
    from sqlalchemy import update
    await db.execute(
        update(User)
        .where(User.referred_by_id == user.id)
        .values(referred_by_id=None)
    )
    
    # Delete the user
    await db.delete(user)
    await db.commit()
    
    return {
        "message": f"User {telegram_id} deleted",
        "status": "ok"
    }


@router.delete(
    "/reset-friendships",
    summary="Reset all friendships",
    description="Deletes all friendships and referral connections. FOR TESTING ONLY.",
    dependencies=[Depends(check_dev_mode)]
)
async def reset_friendships(db: AsyncSession = Depends(get_db)):
    """Delete all friendships and reset referral connections."""
    
    from sqlalchemy import update
    
    # Delete all friendships
    await db.execute(delete(Friendship))
    
    # Reset all referred_by connections
    await db.execute(
        update(User).values(referred_by_id=None)
    )
    
    await db.commit()
    
    return {"message": "All friendships and referral connections reset", "status": "ok"}


@router.post(
    "/reset-all-progress",
    summary="Reset progress for all users",
    description="Resets level, watts, current_xp, and total_xp to default values for ALL users. FOR TESTING ONLY.",
    dependencies=[Depends(check_dev_mode)]
)
async def reset_all_progress(db: AsyncSession = Depends(get_db)):
    """Reset game progress for all users to default values."""
    
    from sqlalchemy import update
    
    # Reset progress fields to defaults
    result = await db.execute(
        update(User).values(
            level=1,
            watts=0,
            current_xp=0,
            total_xp=0
        )
    )
    
    await db.commit()
    
    return {
        "message": f"Progress reset for {result.rowcount} users",
        "status": "ok",
        "affected_users": result.rowcount
    }


@router.post(
    "/reset-all-referrals",
    summary="Reset referral data for all users",
    description="Clears all friendships and referral connections, but keeps user accounts. FOR TESTING ONLY.",
    dependencies=[Depends(check_dev_mode)]
)
async def reset_all_referrals(db: AsyncSession = Depends(get_db)):
    """Reset all referral data: friendships and referred_by connections."""
    
    from sqlalchemy import update
    
    # Delete all friendships
    friendships_result = await db.execute(delete(Friendship))
    
    # Reset all referred_by connections
    users_result = await db.execute(
        update(User).values(referred_by_id=None)
    )
    
    await db.commit()
    
    return {
        "message": "All referral data reset",
        "status": "ok",
        "friendships_deleted": friendships_result.rowcount,
        "referral_connections_cleared": users_result.rowcount
    }


@router.post(
    "/add-resources",
    response_model=AddResourcesResponse,
    summary="Add XP and/or watts to current player",
    description="""
    Debug endpoint to add XP and/or watts to the authenticated player.
    
    Both values must be non-negative. At least one must be greater than 0.
    XP is added to both current_xp and total_xp.
    Watts are added directly to the balance.
    
    Requires authentication (JWT token).
    """,
    dependencies=[Depends(check_dev_mode)]
)
async def add_resources(
    request: AddResourcesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AddResourcesResponse:
    """Add XP and/or watts to the current authenticated player."""
    
    success, progress, added_watts, added_xp, message = await progress_service.add_resources(
        db=db,
        user=current_user,
        watts=request.watts,
        xp=request.xp
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return AddResourcesResponse(
        success=success,
        progress=progress,
        addedWatts=added_watts,
        addedXp=added_xp,
        message=message
    )


