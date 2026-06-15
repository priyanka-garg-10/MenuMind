from langgraph.graph import END, START, StateGraph

from app.agents.customer_id_agent import customer_id_node
from app.agents.preference_agent import preference_node, route_after_customer_id
from app.agents.recommendation_agent import recommendation_node
from app.agents.state import AgentState


def build_graph():
    """
    Compile the Restaurant AI LangGraph.

    Phase 5  → customer_id → END
    Phase 6  → customer_id → (conditional) → preference → END
    Phase 7  → customer_id → (conditional) → preference → recommendation → END

    Control flow
    ------------
    START
      └─► customer_id
               │
          is_new_user?
           YES └─► END          (new visitors skip personalisation)
           NO  └─► preference
                       └─► recommendation
                                 └─► END
    """
    builder = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    builder.add_node("customer_id", customer_id_node)
    builder.add_node("preference", preference_node)
    builder.add_node("recommendation", recommendation_node)

    # ── Define control flow ───────────────────────────────────────────────────
    builder.add_edge(START, "customer_id")

    # Conditional branch: new user → END, returning user → preference
    builder.add_conditional_edges("customer_id", route_after_customer_id)

    # Returning users always go through recommendation after preference
    builder.add_edge("preference", "recommendation")
    builder.add_edge("recommendation", END)

    return builder.compile()


# Singleton — compiled once when this module is first imported.
restaurant_graph = build_graph()
