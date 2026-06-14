from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import restaurant_graph
from app.agents.state import AgentState
from app.core.database import get_db

router = APIRouter()


class IdentifyRequest(BaseModel):
    phone: str


@router.post("/identify")
async def identify_customer(
    payload: IdentifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Run the Customer Identification Agent.

    Accepts a phone number, passes it into the LangGraph as the initial
    state, and returns the full agent state after all nodes have executed.
    """
    initial_state: AgentState = {
        "phone": payload.phone,
        "user_id": None,
        "user_name": None,
        "is_new_user": False,
        "visit_count": 0,
        "preferences": None,
        "health_goals": [],
        "dietary_filters": {},
        "order_history": [],
        "recommendations": [],
        "staff_summary": None,
        "current_step": "start",
        "error": None,
    }

    result: AgentState = await restaurant_graph.ainvoke(
        initial_state,
        config={"configurable": {"db": db}},
    )

    return result
