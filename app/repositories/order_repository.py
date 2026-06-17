from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order


class OrderRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: int, item_id: int, item_name: str) -> Order:
        order = Order(user_id=user_id, item_id=item_id, item_name=item_name)
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_recent_by_user(self, user_id: int, limit: int = 5) -> list[Order]:
        result = await self.db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.ordered_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Order).where(Order.user_id == user_id)
        )
        return result.scalar_one()
