from langgraph.graph import END, START, StateGraph

from app.agents.customer_id_agent import customer_id_node
from app.agents.health_agent import health_agent_node
from app.agents.memory_agent import memory_agent_node
from app.agents.preference_agent import preference_node, route_after_customer_id
from app.agents.recommendation_agent import recommendation_node
from app.agents.state import AgentState


def build_graph():
    """
    Control flow
    ------------
    START
      └─► customer_id
               │
          is_new_user?
           YES └─► END
           NO  └─► preference
                       └─► memory_agent        ← Phase 9
                                 └─► recommendation
                                           └─► health_agent
                                                     └─► END
    """
    builder = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    builder.add_node("customer_id", customer_id_node)
    builder.add_node("preference", preference_node)
    builder.add_node("memory_agent", memory_agent_node)
    builder.add_node("recommendation", recommendation_node)
    builder.add_node("health_agent", health_agent_node)

    # ── Define control flow ───────────────────────────────────────────────────
    builder.add_edge(START, "customer_id")

    # Conditional: new user → END, returning user → preference
    builder.add_conditional_edges("customer_id", route_after_customer_id)

    builder.add_edge("preference", "memory_agent")
    builder.add_edge("memory_agent", "recommendation")
    builder.add_edge("recommendation", "health_agent")
    builder.add_edge("health_agent", END)

    return builder.compile()


# Singleton — compiled once when this module is first imported.
restaurant_graph = build_graph()
