from backend.core.state import OmniResolveState, IntentType, ActionPlan, RiskLevel, AgentThought
from backend.tools.db_tools import lookup_order

async def logistics_node(state: OmniResolveState) -> dict:
    order_id = state.get("order_id")
    if not order_id:
        thought = AgentThought(
            step=len(state.get("agent_trace", [])) + 1,
            agent="Logistics Agent",
            thought="Cannot proceed: No Order ID provided by customer."
        )
        return {
            "final_response": "Could you please provide your Order ID (e.g., ORD-901) so I can assist you?",
            "agent_trace": [thought]
        }
    
    order = lookup_order(order_id)
    if not order:
        thought = AgentThought(
            step=len(state.get("agent_trace", [])) + 1,
            agent="Logistics Agent",
            thought=f"Lookup failed: Order {order_id} does not exist in database."
        )
        return {
            "final_response": f"I was unable to find any order matching ID {order_id}. Please verify the number.",
            "agent_trace": [thought]
        }
    
    intent = state.get("detected_intent")
    
    if intent == IntentType.ORDER_TRACKING:
        tracking_info = order.get("tracking_number") or "Preparing for carrier pickup"
        msg = f"Your order {order_id} ({order['item_name']}) is currently **{order['status']}**. Tracking: `{tracking_info}`. Destination: {order['shipping_address']}."
        thought = AgentThought(
            step=len(state.get("agent_trace", [])) + 1,
            agent="Logistics Agent",
            thought=f"Order {order_id} status is {order['status']}. Returned tracking information.",
            tool_called="lookup_order",
            tool_output=order
        )
        return {"final_response": msg, "agent_trace": [thought]}
        
    elif intent == IntentType.ADDRESS_UPDATE:
        # Extract new address from customer message
        import re
        address_match = re.search(r'to (.*)', state['customer_message'], re.IGNORECASE)
        new_address = address_match.group(1).strip() if address_match else "Updated Address, TX"
        
        action = ActionPlan(
            agent_name="Logistics Agent",
            action_type="UPDATE_ADDRESS",
            parameters={"order_id": order_id, "new_address": new_address, "current_status": order["status"]},
            risk_level=RiskLevel.LOW if order["status"] == "PROCESSING" else RiskLevel.HIGH,
            risk_reasoning=f"Order is in '{order['status']}' state."
        )
        thought = AgentThought(
            step=len(state.get("agent_trace", [])) + 1,
            agent="Logistics Agent",
            thought=f"Prepared ActionPlan to change shipping address for {order_id} to '{new_address}'.",
            tool_called="plan_action",
            tool_output=action.model_dump()
        )
        return {"current_action": action, "agent_trace": [thought]}

    return {}
