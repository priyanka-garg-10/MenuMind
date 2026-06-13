from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menu import MenuItem


class MenuRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, **kwargs) -> MenuItem:
        item = MenuItem(**kwargs)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_by_id(self, item_id: int) -> MenuItem | None:
        result = await self.db.execute(select(MenuItem).where(MenuItem.id == item_id))
        return result.scalar_one_or_none()

    async def get_all(self) -> list[MenuItem]:
        result = await self.db.execute(
            select(MenuItem).where(MenuItem.is_available == True)  # noqa: E712
            .order_by(MenuItem.category, MenuItem.name)
        )
        return list(result.scalars().all())

    async def get_unindexed(self) -> list[MenuItem]:
        """Return items not yet stored in Qdrant (qdrant_id is NULL)."""
        result = await self.db.execute(
            select(MenuItem).where(MenuItem.qdrant_id == None)  # noqa: E711
        )
        return list(result.scalars().all())

    async def update(self, item: MenuItem, **fields) -> MenuItem:
        for key, value in fields.items():
            setattr(item, key, value)
        await self.db.commit()
        await self.db.refresh(item)
        return item
