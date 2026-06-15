from langgraph.graph import END, START, StateGraph

from app.agents.customer_id_agent import customer_id_node
from app.agents.preference_agent import preference_node, route_after_customer_id
from app.agents.state import AgentState


def build_graph():
    """
    Compile the Restaurant AI LangGraph.
    """
    builder = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    builder.add_node("customer_id", customer_id_node)
    builder.add_node("preference", preference_node)

    # ── Define control flow ───────────────────────────────────────────────────
    builder.add_edge(START, "customer_id")

    # Conditional edge: route_after_customer_id reads state["is_new_user"]
    # and returns either "preference" or END.
    # LangGraph calls this function automatically after customer_id finishes.
    builder.add_conditional_edges("customer_id", route_after_customer_id)

    builder.add_edge("preference", END)

    return builder.compile()


# Singleton — compiled once when this module is first imported.
restaurant_graph = build_graph()
