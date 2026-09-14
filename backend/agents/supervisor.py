from pydantic import BaseModel, Field
from typing import Optional
from backend.core.state import OmniResolveState, IntentType, AgentThought
from backend.core.llm_client import call_structured_llm

class SupervisorDecision(BaseModel):
    intent: IntentType = Field(description="Detected primary intent of customer inquiry")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    order_id: Optional[str] = Field(default=None, description="Extracted order ID like ORD-901 if mentioned")
    reasoning: str = Field(description="Brief explanation of why this intent was classified")

async def supervisor_node(state: OmniResolveState) -> dict:
    """
    Supervisor Node: Classifies intent, extracts order IDs, and routes to specialists.
    """
    prompt = f"""
    Analyze this customer support request:
    Customer Message: "{state['customer_message']}"
    Image Attached: {bool(state.get('image_url'))}
    Known Order ID: {state.get('order_id')}
    
    Classify the inquiry into one of:
    - ORDER_TRACKING: Asking where an order is or tracking status
    - ADDRESS_UPDATE: Asking to modify shipping address
    - REFUND_REQUEST: Asking for money back or cancellation
    - DAMAGE_CLAIM: Reporting a broken/damaged product (especially if image is attached)
    - GENERAL_INQUIRY: General questions about policies or store hours
    """
    
    # Fallback heuristic if API key is not present
    fallback_intent = IntentType.GENERAL_INQUIRY
    msg_lower = state['customer_message'].lower()
    if "track" in msg_lower or "where is" in msg_lower:
        fallback_intent = IntentType.ORDER_TRACKING
    elif "address" in msg_lower or "shipping" in msg_lower:
        fallback_intent = IntentType.ADDRESS_UPDATE
    elif "damaged" in msg_lower or "broken" in msg_lower or state.get('image_url'):
        fallback_intent = IntentType.DAMAGE_CLAIM
    elif "refund" in msg_lower or "cancel" in msg_lower:
        fallback_intent = IntentType.REFUND_REQUEST
    
    extracted_order = state.get("order_id")
    if not extracted_order:
        import re
        match = re.search(r'ORD-\d+', state['customer_message'], re.IGNORECASE)
        if match:
            extracted_order = match.group(0).upper()

    decision = await call_structured_llm(
        prompt=prompt,
        output_schema=SupervisorDecision,
        system_instruction="You are an expert customer operations triage supervisor.",
        mock_fallback=SupervisorDecision(
            intent=fallback_intent,
            confidence=0.92,
            order_id=extracted_order,
            reasoning=f"Classified as {fallback_intent.value} based on customer query."
        )
    )
    
    step_thought = AgentThought(
        step=len(state.get("agent_trace", [])) + 1,
        agent="Supervisor Agent",
        thought=f"Intent: {decision.intent.value} (Confidence: {decision.confidence:.2f}). {decision.reasoning}",
        tool_called=None,
        tool_output={"extracted_order_id": decision.order_id or extracted_order}
    )
    
    return {
        "detected_intent": decision.intent,
        "confidence": decision.confidence,
        "intent_reasoning": decision.reasoning,
        "order_id": decision.order_id or extracted_order,
        "agent_trace": [step_thought]
    }
