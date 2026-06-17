from app.agents.state import AgentState
from app.core.logging_config import get_logger

logger = get_logger(__name__)


# Scoring helpers 

def _compute_health_score(item: dict, health_goals: list[str]) -> float:
    """
    Compute a numeric health score for a menu item given the customer's goals.
    """
    calories: float = float(item.get("calories") or 1)
    protein: float = float(item.get("protein_g") or 0.0)

    if not health_goals:
        return round(item.get("score", 0.0) * 10, 3)

    score = 0.0

    if "weight-loss" in health_goals or "low-calorie" in health_goals:
        score += (protein / calories) * 100
        score -= calories / 100

    if "high-protein" in health_goals or "muscle-gain" in health_goals:
        score += protein * 2

    if "fitness" in health_goals:
        score += protein
        score -= calories / 200

    return round(score, 3)


def _find_allergy_conflicts(items: list[dict], allergies: list[str]) -> list[str]:
    """
    Cross-reference each item's tags against the customer's allergy list.
    """
    if not allergies:
        return []

    warnings: list[str] = []
    allergens_lower = [a.strip().lower() for a in allergies]

    for item in items:
        tags = [t.lower() for t in (item.get("tags") or [])]
        name_lower = item.get("name", "").lower()
        for allergen in allergens_lower:
            if allergen in tags or allergen in name_lower:
                warnings.append(
                    f"Warning: '{item['name']}' may contain {allergen} — "
                    f"flagged against this customer's allergy profile."
                )
                break   # one warning per item is enough

    return warnings


#Node

async def health_agent_node(state: AgentState) -> dict:
    """
    Health-Aware Agent — post-retrieval nutritional re-ranking.

    Reads the `recommendations` list retrieved from Qdrant
    and applies two layers of health logic:

    1. Scoring  — computes health_score per item (pure math, no LLM)
    2. Ranking  — re-sorts by health_score so the best fit appears first
    3. Allergy  — cross-references tags against the customer's allergy list
                  and generates human-readable health_warnings
    """
    recommendations: list[dict] = list(state.get("recommendations") or [])
    health_goals: list[str] = state.get("health_goals") or []
    prefs: dict = state.get("preferences") or {}
    allergies: list[str] = prefs.get("allergies") or []

    if not recommendations:
        logger.info("HealthAgent: no recommendations to process")
        return {
            "recommendations": [],
            "health_warnialth_ngs": [],
            "current_step": "hechecked",
        }

    scored: list[dict] = [
        {**item, "health_score": _compute_health_score(item, health_goals)}
        for item in recommendations
    ]

   
    scored.sort(key=lambda x: x["health_score"], reverse=True)

    logger.info(
        "HealthAgent: re-ranked %d items  goals=%s  top='%s' (health_score=%.3f)",
        len(scored),
        health_goals,
        scored[0].get("name"),
        scored[0].get("health_score", 0),
    )

  
    warnings = _find_allergy_conflicts(scored, allergies)
    if warnings:
        for w in warnings:
            logger.warning("HealthAgent: %s", w)

    return {
        "recommendations": scored,
        "health_warnings": warnings,
        "current_step": "health_checked",
    }

