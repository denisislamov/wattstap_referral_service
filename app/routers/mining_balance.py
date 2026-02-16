"""
Mining Balance API endpoints.

Public endpoint: GET /balance/mining — returns active balance config (no auth required).
Admin endpoints: PUT, POST /seed, etc. — require auth + admin check (dev mode only for now).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.mining_balance import (
    MiningBalancePublicResponse,
    MiningBalanceAdminResponse,
    MiningBalanceUpdateRequest,
    MiningBalanceSeedResponse,
)
from app.services.mining_balance_service import mining_balance_service

router = APIRouter(prefix="/balance", tags=["Mining Balance"])


# ──────────────────────────────────────────────
# Public endpoint (no auth) — used by Unity client
# ──────────────────────────────────────────────

@router.get(
    "/mining",
    response_model=MiningBalancePublicResponse,
    summary="Get active mining balance config",
    description="""
    Returns the current active mining balance configuration.
    
    This endpoint is **public** (no authentication required) so the Unity client
    can fetch it during startup before the user has authenticated.
    
    The response format matches the Unity MiningBalanceConfig structure with camelCase fields.
    """,
)
async def get_mining_balance(
    db: AsyncSession = Depends(get_db),
) -> MiningBalancePublicResponse:
    """Return the active mining balance to the client."""
    params = await mining_balance_service.get_active_balance(db)

    if not params:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mining balance config not found. Run seed first.",
        )

    balance = mining_balance_service.params_to_response(params)
    return MiningBalancePublicResponse(success=True, balance=balance)


# ──────────────────────────────────────────────
# Admin endpoints (dev-only for now)
# ──────────────────────────────────────────────

def _check_admin():
    """Simple admin guard — only allow in non-production."""
    if settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin endpoints are disabled in production",
        )


@router.get(
    "/mining/admin",
    response_model=MiningBalanceAdminResponse,
    summary="[Admin] Get balance with metadata",
    dependencies=[Depends(_check_admin)],
)
async def get_mining_balance_admin(
    db: AsyncSession = Depends(get_db),
) -> MiningBalanceAdminResponse:
    """Admin view of the mining balance with version/timestamps."""
    params = await mining_balance_service.get_active_balance(db)

    if not params:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mining balance config not found",
        )

    balance = mining_balance_service.params_to_response(params)
    return MiningBalanceAdminResponse(
        success=True,
        version=params.version,
        isActive=params.is_active,
        balance=balance,
        createdAt=params.created_at.isoformat() if params.created_at else None,
        updatedAt=params.updated_at.isoformat() if params.updated_at else None,
    )


@router.put(
    "/mining/admin",
    response_model=MiningBalanceAdminResponse,
    summary="[Admin] Update mining balance",
    description="Update start parameters and/or daily progression. Only provided fields are changed.",
    dependencies=[Depends(_check_admin)],
)
async def update_mining_balance(
    update: MiningBalanceUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> MiningBalanceAdminResponse:
    """Update mining balance configuration."""
    success, params, message = await mining_balance_service.update_balance(db, update)

    if not success or not params:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    balance = mining_balance_service.params_to_response(params)
    return MiningBalanceAdminResponse(
        success=True,
        version=params.version,
        isActive=params.is_active,
        balance=balance,
        createdAt=params.created_at.isoformat() if params.created_at else None,
        updatedAt=params.updated_at.isoformat() if params.updated_at else None,
    )


@router.post(
    "/mining/seed",
    response_model=MiningBalanceSeedResponse,
    summary="[Admin] Re-seed balance from CSV",
    description="Force re-seed balance from the bundled CSV file. Overwrites existing data.",
    dependencies=[Depends(_check_admin)],
)
async def seed_mining_balance(
    force: bool = True,
    db: AsyncSession = Depends(get_db),
) -> MiningBalanceSeedResponse:
    """Re-seed mining balance from the CSV file."""
    from app.services.mining_balance_service import mining_balance_service as svc

    csv_path = _get_csv_path()
    success, message, days = await svc.seed_from_csv_file(db, csv_path, force=force)

    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

    return MiningBalanceSeedResponse(
        success=True,
        message=message,
        version="default",
        paramsCount=1,
        daysCount=days,
    )


def _get_csv_path() -> str:
    """Resolve the path to the bundled CSV file."""
    import os

    # Try multiple locations
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "WattsBalanceMining.csv"),
        os.path.join(os.path.dirname(__file__), "..", "data", "WattsBalanceMining.csv"),
        "data/WattsBalanceMining.csv",
    ]
    for path in candidates:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            return abs_path

    # Fallback
    return os.path.abspath("data/WattsBalanceMining.csv")
