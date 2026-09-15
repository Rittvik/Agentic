from langgraph.graph import StateGraph, END
from backend.core.state import OmniResolveState, IntentType
from backend.agents.supervisor import supervisor_node
from backend.agents.logistics_agent import logistics_node
from backend.agents.billing_agent import billing_node
from backend.agents.guardrail_agent import guardrail_node
from backend.agents.execution_node import execution_node

def route_intent(state: OmniResolveState) -> str:
    """Conditional Edge router based on supervisor's intent detection."""
    intent = state.get("detected_intent")
    if intent in [IntentType.ORDER_TRACKING, IntentType.ADDRESS_UPDATE]:
        return "logistics_agent"
    elif intent in [IntentType.REFUND_REQUEST, IntentType.DAMAGE_CLAIM]:
        return "billing_agent"
    return "end_node"

def build_omni_resolve_graph():
    """Builds and compiles the master LangGraph Multi-Agent StateGraph."""
    builder = StateGraph(OmniResolveState)
    
    # Add Agent Nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("logistics_agent", logistics_node)
    builder.add_node("billing_agent", billing_node)
    builder.add_node("guardrail_agent", guardrail_node)
    builder.add_node("execution_node", execution_node)
    
    # Define Entry Point
    builder.set_entry_point("supervisor")
    
    # Conditional Edges from Supervisor
    builder.add_conditional_edges(
        "supervisor",
        route_intent,
        {
            "logistics_agent": "logistics_agent",
            "billing_agent": "billing_agent",
            "end_node": END
        }
    )
    
    # Specialists route into the Guardrail Agent
    builder.add_edge("logistics_agent", "guardrail_agent")
    builder.add_edge("billing_agent", "guardrail_agent")
    
    # Guardrail routes into Execution Node
    builder.add_edge("guardrail_agent", "execution_node")
    
    # Execution routes to END
    builder.add_edge("execution_node", END)
    
    return builder.compile()

# Master compiled graph instance
omni_agent_graph = build_omni_resolve_graph()
