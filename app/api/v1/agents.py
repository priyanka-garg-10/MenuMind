from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import restaurant_graph
from app.agents.state import AgentState
from app.core.database import get_db
from app.core.vector_store import get_qdrant_client

router = APIRouter()


class IdentifyRequest(BaseModel):
    phone: str


@router.post("/identify")
async def identify_customer(
    payload: IdentifyRequest,
    db: AsyncSession = Depends(get_db),
    qdrant: AsyncQdrantClient = Depends(get_qdrant_client),
):
    """
    Run the full Restaurant AI agent pipeline for a given phone number.
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
        "recommendation_text": None,
        "health_warnings": [],
        "staff_summary": None,
        "current_step": "start",
        "error": None,
    }

    try:
        result: AgentState = await restaurant_graph.ainvoke(
            initial_state,
            config={"configurable": {"db": db, "qdrant": qdrant}},
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Agent pipeline failed — Qdrant may be unavailable: {exc}",
        )
