from fastapi import APIRouter, Depends
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

    Phase 5  – Customer ID node identifies the caller.
    Phase 6  – Preference node enriches dietary filters (returning users only).
    Phase 7  – Recommendation node runs RAG and generates a GPT recommendation.

    New visitor response
    --------------------
    is_new_user: true, recommendations: [], recommendation_text: null
    current_step: "customer_identified"

    Returning user response
    -----------------------
    is_new_user: false, recommendations: [list of top menu items]
    recommendation_text: "Here are 3 dishes I recommend for you…"
    current_step: "recommendation_done"
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
        "staff_summary": None,
        "current_step": "start",
        "error": None,
    }

    result: AgentState = await restaurant_graph.ainvoke(
        initial_state,
        config={"configurable": {"db": db, "qdrant": qdrant}},
    )

    return result
