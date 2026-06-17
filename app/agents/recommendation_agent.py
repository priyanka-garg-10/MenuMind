from langchain_core.runnables import RunnableConfig
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient

from app.agents.state import AgentState
from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.rag.embedder import Embedder
from app.rag.retriever import MenuRetriever

logger = get_logger(__name__)
settings = get_settings()

_SYSTEM_PROMPT = (
    "You are a warm, knowledgeable restaurant assistant for an Indian restaurant. "
    "Given a customer's dietary profile and a list of available dishes, "
    "recommend exactly 3 dishes and explain in one sentence why each suits this customer. "
    "Be specific — reference the dish name, a key ingredient, or a nutritional fact. "
    "Keep the total response under 150 words."
)



def _build_search_query(state: AgentState) -> str:
    """
    Construct a natural-language query from the user's preference profile.
    """
    parts: list[str] = []
    prefs: dict = state.get("preferences") or {}

    diet_type = prefs.get("diet_type", "")
    if diet_type in ("veg", "vegan", "jain"):
        parts.append("vegetarian")
    elif diet_type == "non_veg":
        parts.append("non-vegetarian")

    goal_terms: dict[str, str] = {
        "weight-loss":  "light low-calorie healthy",
        "low-calorie":  "low calorie light",
        "high-protein": "high protein",
        "fitness":      "nutritious protein-rich",
        "muscle-gain":  "high protein muscle building",
    }
    for goal in state.get("health_goals", []):
        if goal in goal_terms:
            parts.append(goal_terms[goal])

    cuisines = prefs.get("favorite_cuisines", [])
    if cuisines:
        parts.append(cuisines[0])

    parts.append("food dish")
    return " ".join(parts) if parts else "popular recommended Indian food"


def _format_items_for_prompt(items: list[dict]) -> str:
    """Render retrieved menu items as a numbered list for the GPT prompt."""
    lines: list[str] = []
    for i, item in enumerate(items, 1):
        veg_label = "Veg" if item.get("is_veg") else "Non-veg"
        lines.append(
            f"{i}. {item['name']} ({veg_label}) — "
            f"{item.get('calories', '?')} kcal, "
            f"{item.get('protein_g', '?')}g protein, "
            f"₹{item.get('price', '?')} — "
            f"spice: {item.get('spice_level', 'medium')} — "
            f"relevance score: {item.get('score', '?')}"
        )
    return "\n".join(lines)


async def recommendation_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    Recommendation Agent — the full RAG loop as a LangGraph node.

    R — Retrieve: semantic search on Qdrant with dietary_filters
    A — Augment:  format retrieved items as prompt context
    G — Generate: GPT produces a personalised recommendation

    Dependencies injected via RunnableConfig
    ----------------------------------------
    qdrant: AsyncQdrantClient — passed from the FastAPI route via
            config={"configurable": {"qdrant": qdrant_client}}
    """
    qdrant: AsyncQdrantClient = config["configurable"]["qdrant"]

    prefs: dict = state.get("preferences") or {}
    dietary_filters: dict = state.get("dietary_filters", {})
    health_goals: list[str] = state.get("health_goals", [])

    # ── Step 1: Build search query ─────────────────────────────────────────────
    query = _build_search_query(state)
    logger.info(
        "RecommendationAgent: query=%r  filters=%s", query, dietary_filters
    )

    # ── Step 2: Retrieve from Qdrant ───────────────────────────────────────────
    embedder = Embedder()
    retriever = MenuRetriever(qdrant, embedder)

    retrieved_items = await retriever.search(
        query=query,
        limit=5,
        is_veg=dietary_filters.get("is_veg"),
        cuisine=dietary_filters.get("cuisine"),
        max_calories=dietary_filters.get("max_calories"),
        min_protein=dietary_filters.get("min_protein"),
    )

    logger.info("RecommendationAgent: %d items retrieved from Qdrant", len(retrieved_items))

    if not retrieved_items:
        return {
            "recommendations": [],
            "recommendation_text": (
                "I couldn't find dishes that match your current preferences. "
                "Please ask your waiter for personalised assistance."
            ),
            "current_step": "recommendation_done",
        }

    # ── Step 3: Generate personalised recommendation via GPT ──────────────────
    order_history: list[dict] = state.get("order_history") or []
    visit_count: int = state.get("visit_count") or 0

    # Build order history context so GPT can avoid repetition
    history_line = ""
    if order_history:
        past = ", ".join(
            f"{o['name']} ({o['ordered_at']})" for o in order_history[:3]
        )
        history_line = f"Recent orders: {past}\n"

    visit_line = ""
    if visit_count > 0:
        visit_line = (
            f"This is visit #{visit_count + 1} "
            f"({'loyal customer' if visit_count >= 3 else 'returning customer'}).\n"
        )

    user_message = (
        f"Customer name: {state.get('user_name') or 'Guest'}\n"
        f"Diet type: {prefs.get('diet_type', 'no preference')}\n"
        f"Spice preference: {prefs.get('spice_level', 'medium')}\n"
        f"Health goals: {', '.join(health_goals) if health_goals else 'none'}\n"
        f"Allergies: {', '.join(prefs.get('allergies', [])) or 'none'}\n"
        f"{history_line}"
        f"{visit_line}"
        f"\nAvailable dishes (ranked by relevance):\n"
        f"{_format_items_for_prompt(retrieved_items)}\n\n"
        f"Recommend the 3 best dishes for this customer and explain why each suits them. "
        f"{'If they have recent orders, prefer dishes they have not tried recently.' if order_history else ''}"
    )

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=400,
    )

    recommendation_text: str = response.choices[0].message.content.strip()
    logger.info(
        "RecommendationAgent: generated %d chars", len(recommendation_text)
    )

    return {
        "recommendations": retrieved_items,
        "recommendation_text": recommendation_text,
        "current_step": "recommendation_done",
    }
