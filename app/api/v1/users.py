from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.user_schemas import (
    PreferenceRequest,
    PreferenceResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated user's profile."""
    return await UserService(db).get_profile(user_id)


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    payload: UpdateProfileRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update name or email. Only provided fields are changed."""
    return await UserService(db).update_profile(user_id, payload)


@router.get("/me/preferences", response_model=PreferenceResponse | None)
async def get_my_preferences(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Return the user's saved preferences, or null if none saved yet."""
    return await UserService(db).get_preferences(user_id)


@router.put("/me/preferences", response_model=PreferenceResponse)
async def save_my_preferences(
    payload: PreferenceRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create or fully replace the user's preference profile."""
    return await UserService(db).save_preferences(user_id, payload)
