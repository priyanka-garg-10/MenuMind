import requests
from config import API_BASE


def run_agent_pipeline(token: str, phone: str) -> tuple[dict, int]:
    """
    POST /api/v1/agents/identify

    Triggers the full 6-agent LangGraph pipeline:
      1. customer_id    — identify the customer by phone
      2. preference     — build Qdrant dietary_filters
      3. memory_agent   — load order history + visit count
      4. recommendation — RAG: Qdrant search + GPT generation
      5. health_agent   — nutritional re-ranking + allergy check
      6. waiter_copilot — synthesise staff briefing

    Returns the complete AgentState as a dict:
      user_id, user_name, is_new_user, visit_count,
      preferences, health_goals, dietary_filters,
      order_history, recommendations, recommendation_text,
      health_warnings, staff_summary, current_step, error

    Note: this call involves an OpenAI embedding + GPT call so it may
    take 3-8 seconds. The UI should show a spinner.
    """
    try:
        resp = requests.post(
            f"{API_BASE}/v1/agents/identify",
            json={"phone": phone},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,   # generous timeout for two GPT calls + Qdrant search
        )
        try:
            return resp.json(), resp.status_code
        except Exception:
            return {"detail": f"Server error ({resp.status_code}) — Qdrant may be unavailable."}, resp.status_code
    except requests.exceptions.ConnectionError:
        return {"detail": "Cannot reach the backend."}, 503
    except requests.exceptions.Timeout:
        return {"detail": "The AI pipeline timed out. Please try again."}, 504
