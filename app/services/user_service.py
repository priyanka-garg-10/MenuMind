from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preference import DietType, SpiceLevel
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user_schemas import (
    PreferenceRequest,
    PreferenceResponse,
    UpdateProfileRequest,
    UserResponse,
)


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.user_repo = UserRepository(db)
        self.pref_repo = PreferenceRepository(db)

    async def get_profile(self, user_id: int) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserResponse.model_validate(user)

    async def update_profile(self, user_id: int, data: UpdateProfileRequest) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        updates = data.model_dump(exclude_none=True)
        if updates:
            user = await self.user_repo.update(user, **updates)

        return UserResponse.model_validate(user)

    async def get_preferences(self, user_id: int) -> PreferenceResponse | None:
        pref = await self.pref_repo.get_by_user_id(user_id)
        return PreferenceResponse.model_validate(pref) if pref else None

    async def save_preferences(self, user_id: int, data: PreferenceRequest) -> PreferenceResponse:
        existing = await self.pref_repo.get_by_user_id(user_id)

        if existing is None:
            pref = await self.pref_repo.create(
                user_id=user_id,
                diet_type=data.diet_type,
                spice_level=data.spice_level,
                favorite_cuisines=data.favorite_cuisines,
                allergies=data.allergies,
                health_goals=data.health_goals,
            )
        else:
            pref = await self.pref_repo.update(
                existing,
                diet_type=data.diet_type,
                spice_level=data.spice_level,
                favorite_cuisines=data.favorite_cuisines,
                allergies=data.allergies,
                health_goals=data.health_goals,
            )

        return PreferenceResponse.model_validate(pref)
