from backend.core.state import OmniResolveState, ActionPlan, RiskLevel, AgentThought
from backend.tools.db_tools import lookup_order

async def billing_node(state: OmniResolveState) -> dict:
    order_id = state.get("order_id")
    if not order_id:
        thought = AgentThought(
            step=len(state.get("agent_trace", [])) + 1,
            agent="Billing Agent",
            thought="Cannot process claim: Order ID missing."
        )
        return {
            "final_response": "Please provide your Order ID so I can look up the transaction and evaluate your refund request.",
            "agent_trace": [thought]
        }
    
    order = lookup_order(order_id)
    if not order:
        thought = AgentThought(
            step=len(state.get("agent_trace", [])) + 1,
            agent="Billing Agent",
            thought=f"Order {order_id} not found."
        )
        return {
            "final_response": f"Order {order_id} could not be located in our billing system.",
            "agent_trace": [thought]
        }
    
    amount = order["amount"]
    has_image = bool(state.get("image_url"))
    
    action = ActionPlan(
        agent_name="Billing Agent",
        action_type="PROCESS_REFUND",
        parameters={
            "order_id": order_id,
            "amount": amount,
            "item_name": order["item_name"],
            "has_damage_photo": has_image,
            "customer_trust_score": order["trust_score"]
        },
        risk_level=RiskLevel.LOW, # Will be strictly evaluated by Guardrail Agent next!
        risk_reasoning=f"Customer requesting full refund for {order['item_name']} (${amount})."
    )
    
    thought = AgentThought(
        step=len(state.get("agent_trace", [])) + 1,
        agent="Billing Agent",
        thought=f"Formulated refund proposal for order {order_id}: ${amount:.2f}. Image provided: {has_image}.",
        tool_called="propose_refund",
        tool_output=action.model_dump()
    )
    
    return {"current_action": action, "agent_trace": [thought]}
