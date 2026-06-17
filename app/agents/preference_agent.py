from langgraph.graph import END

from app.agents.state import AgentState
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def route_after_customer_id(state: AgentState) -> str:
    """
    Called by LangGraph immediately after the customer_id node finishes.
    Returns the name of the next node to run.
    """
    if state["is_new_user"]:
        logger.info("Router: new visitor — skipping preference enrichment")
        return END
    logger.info("Router: returning user — enriching preferences")
    return "preference"

async def preference_node(state: AgentState) -> dict:
    """
    Preference Agent — translates raw DB preferences into Qdrant-ready filters.
    """
    prefs: dict | None = state.get("preferences")

    if prefs is None:
        logger.info("PreferenceAgent: no preferences on file — using empty filters")
        return {
            "dietary_filters": {},
            "health_goals": [],
            "current_step": "preference_enriched",
        }

    dietary_filters: dict = {}

    # Diet type → is_veg Qdrant filter
    diet_type: str = prefs.get("diet_type", "")
    if diet_type in ("veg", "vegan", "jain"):
        dietary_filters["is_veg"] = True

    # Favourite cuisine → cuisine Qdrant filter
    cuisines: list[str] = prefs.get("favorite_cuisines", [])
    if cuisines:
        dietary_filters["cuisine"] = cuisines[0]

    # Health goals stay in state for the Health Agent to use during re-ranking.
    health_goals: list[str] = prefs.get("health_goals", [])

    logger.info(
        "PreferenceAgent: dietary_filters=%s  health_goals=%s",
        dietary_filters, health_goals,
    )

    return {
        "dietary_filters": dietary_filters,
        "health_goals": health_goals,
        "current_step": "preference_enriched",
    }
