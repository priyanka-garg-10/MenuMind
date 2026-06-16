from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import AgentState
from app.core.logging_config import get_logger
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.user_repository import UserRepository

logger = get_logger(__name__)


async def customer_id_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    Customer Identification Agent — first node in the restaurant graph.

    Responsibilities
    ----------------
    1. Look up the user by phone number.
    2. Fetch their preference profile if it exists.
    3. Return a partial state update so the next node knows:
       - who the customer is (user_id, user_name)
       - whether they are new or returning (is_new_user)
       - what their dietary preferences are
    """
  
    db: AsyncSession = config["configurable"]["db"]
    phone: str = state["phone"]

    logger.info("CustomerIDAgent: looking up phone=%s", phone)

    user_repo = UserRepository(db)
    pref_repo = PreferenceRepository(db)

    # Lookup 
    user = await user_repo.get_by_phone(phone)

    if user is None:
        logger.info("CustomerIDAgent: new visitor — phone=%s not found", phone)
        return {
            "user_id": None,
            "user_name": None,
            "is_new_user": True,
            "visit_count": 0,
            "preferences": None,
            "health_goals": [],
            "dietary_filters": {},
            "order_history": [],
            "current_step": "customer_identified",
            "error": None,
        }

    # Existing user — fetch preferences
    pref = await pref_repo.get_by_user_id(user.id)

    preferences_dict: dict | None = None
    health_goals: list[str] = []
    dietary_filters: dict = {}

    if pref is not None:
        raw_goals = pref.health_goals or []
        health_goals = [g.replace("_", "-") for g in raw_goals]

        preferences_dict = {
            "diet_type": pref.diet_type.value,
            "spice_level": pref.spice_level.value,
            "favorite_cuisines": pref.favorite_cuisines or [],
            "allergies": pref.allergies or [],
            "health_goals": health_goals,    # already normalised
        }

        # Pre-build dietary_filters used by the Qdrant retriever in Phase 7
        dietary_filters = {
            "is_veg": pref.diet_type.value in ("veg", "vegan", "jain"),
        }
        if pref.favorite_cuisines:
            dietary_filters["cuisine"] = pref.favorite_cuisines[0]

    logger.info(
        "CustomerIDAgent: returning user user_id=%s name=%s has_preferences=%s",
        user.id, user.name, pref is not None,
    )

    return {
        "user_id": user.id,
        "user_name": user.name,
        "is_new_user": False,
        "visit_count": 0,
        "preferences": preferences_dict,
        "health_goals": health_goals,
        "dietary_filters": dietary_filters,
        "order_history": [],
        "current_step": "customer_identified",
        "error": None,
    }
