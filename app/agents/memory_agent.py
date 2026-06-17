from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import AgentState
from app.core.logging_config import get_logger
from app.repositories.order_repository import OrderRepository

logger = get_logger(__name__)


async def memory_agent_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    Memory Agent — loads long-term customer history from MySQL.

    Runs before the Recommendation Agent so that order history
    is available when building the GPT prompt.
    """
    db: AsyncSession = config["configurable"]["db"]
    user_id: int | None = state.get("user_id")

    if user_id is None:
        return {
            "visit_count": 0,
            "order_history": [],
            "current_step": "memory_loaded",
        }

    order_repo = OrderRepository(db)

    recent_orders = await order_repo.get_recent_by_user(user_id, limit=5)
    total_orders = await order_repo.count_by_user(user_id)

    order_history = [
        {
            "name": o.item_name,
            "item_id": o.item_id,
            "ordered_at": o.ordered_at.strftime("%Y-%m-%d"),
        }
        for o in recent_orders
    ]

    logger.info(
        "MemoryAgent: user_id=%s  total_orders=%s  recent=%s",
        user_id,
        total_orders,
        [o["name"] for o in order_history],
    )

    return {
        "visit_count": total_orders,
        "order_history": order_history,
        "current_step": "memory_loaded",
    }
