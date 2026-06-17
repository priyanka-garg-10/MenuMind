from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.repositories.menu_repository import MenuRepository
from app.repositories.order_repository import OrderRepository

router = APIRouter()


class CreateOrderRequest(BaseModel):
    item_ids: list[int]


@router.post("/", status_code=201)
async def create_order(
    payload: CreateOrderRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Record that the authenticated user ordered one or more menu items.
    Each item_id becomes a separate order row so the Memory Agent can
    track individual dish history.
    """
    if not payload.item_ids:
        raise HTTPException(status_code=422, detail="item_ids cannot be empty")

    menu_repo = MenuRepository(db)
    order_repo = OrderRepository(db)
    created = []

    for item_id in payload.item_ids:
        item = await menu_repo.get_by_id(item_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"Menu item {item_id} not found")
        order = await order_repo.create(
            user_id=user_id,
            item_id=item.id,
            item_name=item.name,
        )
        created.append({
            "id": order.id,
            "item_id": order.item_id,
            "item_name": order.item_name,
            "ordered_at": order.ordered_at,
        })

    return {"orders": created, "total": len(created)}


@router.get("/my")
async def get_my_orders(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Return the last 10 orders for the authenticated user."""
    orders = await OrderRepository(db).get_recent_by_user(user_id, limit=10)
    return [
        {
            "id": o.id,
            "item_id": o.item_id,
            "item_name": o.item_name,
            "ordered_at": o.ordered_at,
        }
        for o in orders
    ]
