from backend.core.state import OmniResolveState, RiskLevel, AgentThought
from backend.core.config import settings

async def guardrail_node(state: OmniResolveState) -> dict:
    action = state.get("current_action")
    if not action:
        return {}
    
    requires_hitl = False
    reasons = []
    
    # Policy Rule 1: Address change cannot happen if order already shipped
    if action.action_type == "UPDATE_ADDRESS":
        status = action.parameters.get("current_status")
        if status != "PROCESSING":
            action.risk_level = RiskLevel.HIGH
            requires_hitl = True
            reasons.append(f"Policy Violation: Order is already '{status}'. Cannot change address autonomously.")
        else:
            action.risk_level = RiskLevel.LOW
            reasons.append("Address change permitted: Order is in PROCESSING status.")
            
    # Policy Rule 2: Refund Amount limit ($50 cap for autonomous refunds)
    elif action.action_type == "PROCESS_REFUND":
        amount = action.parameters.get("amount", 0.0)
        trust_score = action.parameters.get("customer_trust_score", 1.0)
        
        if amount > settings.AUTO_REFUND_LIMIT:
            action.risk_level = RiskLevel.HIGH
            requires_hitl = True
            reasons.append(f"Refund amount (${amount:.2f}) exceeds autonomous limit (${settings.AUTO_REFUND_LIMIT:.2f}).")
        
        if trust_score < 0.50:
            action.risk_level = RiskLevel.HIGH
            requires_hitl = True
            reasons.append(f"Customer trust score ({trust_score:.2f}) is below security threshold (0.50).")
            
        if not requires_hitl:
            action.risk_level = RiskLevel.LOW
            reasons.append("Refund is under $50 threshold and customer has good trust score. Autonomous approval granted.")
    
    action.requires_hitl = requires_hitl
    action.risk_reasoning = " | ".join(reasons)
    
    thought = AgentThought(
        step=len(state.get("agent_trace", [])) + 1,
        agent="Guardrail Agent",
        thought=f"Risk Evaluation: {action.risk_level.value}. Requires Human Approval: {requires_hitl}. Reason: {action.risk_reasoning}",
        tool_called="evaluate_policy",
        tool_output={"risk_level": action.risk_level.value, "requires_hitl": requires_hitl}
    )
    
    return {"current_action": action, "agent_trace": [thought]}
