from backend.core.state import OmniResolveState, TicketStatus, AgentThought
from backend.tools.db_tools import update_shipping_address, process_refund
from backend.tools.n8n_tools import dispatch_hitl_to_n8n, dispatch_resolution_to_n8n

async def execution_node(state: OmniResolveState) -> dict:
    action = state.get("current_action")
    if not action:
        # If there's already a final response (like tracking lookup), nothing to execute
        return {"status": TicketStatus.RESOLVED}
    
    # Check if this requires Human-in-the-Loop approval and hasn't been approved yet
    if action.requires_hitl and state.get("status") != TicketStatus.APPROVED:
        # Trigger n8n HITL Webhook for Slack/Email card
        await dispatch_hitl_to_n8n(
            ticket_id=state["ticket_id"],
            action_plan=action.model_dump(),
            customer_message=state["customer_message"],
            customer_info={"order_id": state.get("order_id")}
        )
        
        thought = AgentThought(
            step=len(state.get("agent_trace", [])) + 1,
            agent="Execution Engine",
            thought=f"Action paused: Dispatched HITL approval request to n8n. Awaiting supervisor decision.",
            tool_called="dispatch_hitl_to_n8n",
            tool_output={"ticket_id": state["ticket_id"], "status": "PENDING_HUMAN_APPROVAL"}
        )
        
        return {
            "status": TicketStatus.PENDING_HUMAN_APPROVAL,
            "final_response": "Your request requires manager authorization due to company policy. A supervisor has been notified via n8n and will review your request shortly.",
            "agent_trace": [thought]
        }
    
    # Autonomous Execution or Human Approved!
    result = {}
    if action.action_type == "UPDATE_ADDRESS":
        result = update_shipping_address(
            order_id=action.parameters["order_id"],
            new_address=action.parameters["new_address"]
        )
        if result.get("success"):
            response = f"Successfully updated your shipping address for Order {action.parameters['order_id']} to **{action.parameters['new_address']}**."
        else:
            response = f"Could not update shipping address: {result.get('error')}"
            
    elif action.action_type == "PROCESS_REFUND":
        result = process_refund(
            order_id=action.parameters["order_id"],
            amount=action.parameters["amount"],
            reason="Customer claim approved."
        )
        if result.get("success"):
            response = f"A full refund of **${action.parameters['amount']:.2f}** has been processed for Order {action.parameters['order_id']} (Transaction Ref: `{result['transaction_id']}`)."
        else:
            response = f"Refund could not be processed: {result.get('error')}"
    else:
        response = "Action could not be recognized."

    # Dispatch completion to n8n CRM/Notion sync
    await dispatch_resolution_to_n8n(
        ticket_id=state["ticket_id"],
        summary=response,
        resolution_details={"action": action.model_dump(), "execution_result": result}
    )
    
    thought = AgentThought(
        step=len(state.get("agent_trace", [])) + 1,
        agent="Execution Engine",
        thought=f"Tool executed successfully: {action.action_type}. Dispatched resolution event to n8n.",
        tool_called=action.action_type,
        tool_output=result
    )
    
    return {
        "status": TicketStatus.RESOLVED,
        "final_response": response,
        "agent_trace": [thought]
    }
