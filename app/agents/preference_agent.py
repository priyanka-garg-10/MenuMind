from langgraph.graph import END

from app.agents.state import AgentState
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Health goal strings → Qdrant filter keys.
# Multiple goals can apply at once; the most restrictive value wins.
_HEALTH_GOAL_FILTERS: dict[str, dict] = {
    "weight-loss":  {"max_calories": 400},
    "low-calorie":  {"max_calories": 350},
    "high-protein": {"min_protein": 25.0},
    "fitness":      {"min_protein": 20.0},
    "muscle-gain":  {"min_protein": 30.0},
}

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

    # Health goals → calorie / protein Qdrant filters
    health_goals: list[str] = prefs.get("health_goals", [])
    for goal in health_goals:
        mapping = _HEALTH_GOAL_FILTERS.get(goal, {})
        for key, value in mapping.items():
            if key == "max_calories":
                dietary_filters[key] = min(dietary_filters.get(key, 9_999), value)
            elif key == "min_protein":
                dietary_filters[key] = max(dietary_filters.get(key, 0.0), value)

    logger.info(
        "PreferenceAgent: dietary_filters=%s  health_goals=%s",
        dietary_filters, health_goals,
    )

    return {
        "dietary_filters": dietary_filters,
        "health_goals": health_goals,
        "current_step": "preference_enriched",
    }
