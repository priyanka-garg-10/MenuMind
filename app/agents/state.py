from typing import TypedDict


class AgentState(TypedDict):
    """
    Shared state object that flows through every node in the LangGraph.

    Each agent reads from this state and returns a dict with the keys it
    updated.  LangGraph merges those updates back — so nodes only need to
    return the fields they change, not the entire state.

    """

   
    phone: str

    # ── Customer ID Agent ─────────────────────────────────────────────────────
    user_id: int | None
    user_name: str | None
    is_new_user: bool
    visit_count: int

    # ── Preference / Health data ───────────────────────────────────────────────
    preferences: dict | None
    health_goals: list[str]
    dietary_filters: dict

    # ── Memory Agent ──────────────────────────────────────────────────────────
    order_history: list[dict]

    # ── Recommendation Agent ──────────────────────────────────────────────────
    recommendations: list[dict]         # Raw Qdrant results (name, score, calories, …)
    recommendation_text: str | None     # GPT-generated personalised recommendation

    # ── Waiter Copilot ────────────────────────────────────────────────────────
    staff_summary: str | None

    # ── Graph meta ────────────────────────────────────────────────────────────
    current_step: str
    error: str | None
