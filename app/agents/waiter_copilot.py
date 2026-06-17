from openai import AsyncOpenAI

from app.agents.state import AgentState
from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

_SYSTEM_PROMPT = (
    "You are a restaurant management AI that generates concise staff briefings. "
    "Write a 4-6 line note for the waiter — professional shorthand, no fluff. "
    "Structure: customer context line, dietary/allergy line, "
    "top dish suggestions with one-word reasons, upsell opportunity if any. "
    "Use ⚠ for allergy warnings. Never address the customer directly — "
    "this is for the waiter's eyes only. Stay under 80 words."
)


def _format_top_recommendations(recommendations: list[dict], n: int = 3) -> str:
    if not recommendations:
        return "none available"
    lines = []
    for item in recommendations[:n]:
        lines.append(
            f"{item['name']} "
            f"({item.get('calories', '?')} kcal, "
            f"{item.get('protein_g', '?')}g protein, "
            f"health_score={item.get('health_score', '?')})"
        )
    return " | ".join(lines)


async def waiter_copilot_node(state: AgentState) -> dict:
    """
    Waiter Copilot — final synthesis node.

    Reads the fully populated AgentState and generates a short staff briefing
    that the waiter sees before approaching the table.

    No DB or Qdrant access needed — every field required is already in state,
    populated by the 5 preceding agents.
    """
    prefs: dict = state.get("preferences") or {}
    recommendations: list[dict] = state.get("recommendations") or []
    health_warnings: list[str] = state.get("health_warnings") or []
    order_history: list[dict] = state.get("order_history") or []
    visit_count: int = state.get("visit_count") or 0
    user_name: str = state.get("user_name") or "Guest"

    # Build context for prompt 
    visit_label = (
        "first-time visitor" if visit_count == 0
        else f"returning — visit #{visit_count + 1}"
        + (" (loyal)" if visit_count >= 3 else "")
    )

    allergies = prefs.get("allergies") or []
    allergy_line = f"⚠ Allergies: {', '.join(allergies)}" if allergies else "No known allergies"

    past_orders = (
        ", ".join(o["name"] for o in order_history[:3])
        if order_history else "none on record"
    )

    top_dishes = _format_top_recommendations(recommendations, n=3)

    warning_block = (
        "\n".join(health_warnings) if health_warnings
        else "No health conflicts detected"
    )

    user_message = (
        f"Customer: {user_name} | {visit_label}\n"
        f"Diet: {prefs.get('diet_type', 'unknown')} | "
        f"Spice: {prefs.get('spice_level', 'medium')}\n"
        f"Health goals: {', '.join(state.get('health_goals') or []) or 'none'}\n"
        f"{allergy_line}\n"
        f"Previous orders: {past_orders}\n"
        f"Top recommendations (health-ranked): {top_dishes}\n"
        f"Health warnings: {warning_block}\n\n"
        f"Write the staff briefing."
    )

    logger.info("WaiterCopilot: generating staff summary for user=%s", user_name)

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.4,
        max_tokens=200,
    )

    staff_summary: str = response.choices[0].message.content.strip()
    logger.info("WaiterCopilot: generated %d chars", len(staff_summary))

    return {
        "staff_summary": staff_summary,
        "current_step": "waiter_briefing_ready",
    }