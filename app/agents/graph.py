from langgraph.graph import END, START, StateGraph

from app.agents.customer_id_agent import customer_id_node
from app.agents.state import AgentState


def build_graph():
    """
    Compile the Restaurant AI LangGraph.
    """
    builder = StateGraph(AgentState)

    # ── Register nodes 
    builder.add_node("customer_id", customer_id_node)

    # ── Define control flow
    # START → customer_id → END
    builder.add_edge(START, "customer_id")
    builder.add_edge("customer_id", END)

    return builder.compile()


# Singleton — compiled once when this module is first imported.
restaurant_graph = build_graph()
