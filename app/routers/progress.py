"""
Player progress API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.progress import (
    LoadProgressResponse,
    ResetProgressRequest,
    ResetProgressResponse,
    SaveProgressRequest,
    SaveProgressResponse,
)
from app.services.progress_service import progress_service

router = APIRouter(prefix="/progress", tags=["Player Progress"])


@router.get(
    "",
    response_model=LoadProgressResponse,
    summary="Load player progress",
    description="""
    Load the current player's progress from the server.
    
    Returns the saved progress data including level, watts, and experience.
    If the player is new (no saved progress), default values are returned.
    """
)
async def load_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> LoadProgressResponse:
    """
    Load player progress from server.
    
    Returns saved progress or default values for new players.
    """
    progress = progress_service.get_progress(current_user)
    is_new = progress_service.is_new_player(current_user)
    
    return LoadProgressResponse(
        success=True,
        progress=progress,
        isNewPlayer=is_new
    )


@router.post(
    "",
    response_model=SaveProgressResponse,
    summary="Save player progress",
    description="""
    Save the current player's progress to the server.
    
    This endpoint should be called periodically (e.g., every 5-8 seconds) 
    to sync the player's progress with the server.
    
    Note: Some anti-cheat validations are applied:
    - Level can only increase
    - Total XP can only increase
    """
)
async def save_progress(
    request: SaveProgressRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SaveProgressResponse:
    """
    Save player progress to server.
    """
    success, progress, message = await progress_service.save_progress(
        db=db,
        user=current_user,
        level=request.level,
        watts=request.watts,
        current_xp=request.current_xp,
        total_xp=request.total_xp
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )
    
    return SaveProgressResponse(
        success=success,
        progress=progress,
        message=message
    )


@router.post(
    "/reset",
    response_model=ResetProgressResponse,
    summary="Reset player progress",
    description="""
    Reset the current player's progress to default values.
    
    **Warning:** This action is irreversible! All progress will be lost.
    
    The `confirm` field must be set to `true` to proceed with the reset.
    """
)
async def reset_progress(
    request: ResetProgressRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ResetProgressResponse:
    """
    Reset player progress to default values.
    """
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset confirmation required. Set 'confirm' to true to proceed."
        )
    
    success, progress, message = await progress_service.reset_progress(
        db=db,
        user=current_user
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )
    
    return ResetProgressResponse(
        success=success,
        progress=progress,
        message=message
    )

