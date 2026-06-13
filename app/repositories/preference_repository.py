from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preference import DietType, SpiceLevel, UserPreference


class PreferenceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_user_id(self, user_id: int) -> UserPreference | None:
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: int,
        diet_type: DietType,
        spice_level: SpiceLevel = SpiceLevel.MEDIUM,
        favorite_cuisines: list[str] | None = None,
        allergies: list[str] | None = None,
        health_goals: list[str] | None = None,
    ) -> UserPreference:
        pref = UserPreference(
            user_id=user_id,
            diet_type=diet_type,
            spice_level=spice_level,
            favorite_cuisines=favorite_cuisines,
            allergies=allergies,
            health_goals=health_goals,
        )
        self.db.add(pref)
        await self.db.commit()
        await self.db.refresh(pref)
        return pref

    async def update(self, pref: UserPreference, **fields) -> UserPreference:
        for key, value in fields.items():
            setattr(pref, key, value)
        await self.db.commit()
        await self.db.refresh(pref)
        return pref
