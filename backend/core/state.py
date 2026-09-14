import operator
from enum import Enum
from typing import List, Dict, Any, Optional, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

class IntentType(str, Enum):
    ORDER_TRACKING = "ORDER_TRACKING"
    ADDRESS_UPDATE = "ADDRESS_UPDATE"
    REFUND_REQUEST = "REFUND_REQUEST"
    DAMAGE_CLAIM = "DAMAGE_CLAIM"
    GENERAL_INQUIRY = "GENERAL_INQUIRY"
    UNKNOWN = "UNKNOWN"

class RiskLevel(str, Enum):
    LOW = "LOW"          # Autonomous execution allowed (e.g. tracking check, address change before dispatch)
    MEDIUM = "MEDIUM"    # Requires strict validation (e.g. low-value store credit < $30)
    HIGH = "HIGH"        # Mandatory Human Approval required (e.g. cash refund > $50, high-value claim)

class TicketStatus(str, Enum):
    PROCESSING = "PROCESSING"
    PENDING_HUMAN_APPROVAL = "PENDING_HUMAN_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RESOLVED = "RESOLVED"

class ActionPlan(BaseModel):
    """Structured decision produced by specialist agents before tool execution."""
    agent_name: str
    action_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    risk_reasoning: str = ""
    requires_hitl: bool = False

class AgentThought(BaseModel):
    """Trace of agent reasoning for dashboard visualization and audit logging."""
    step: int
    agent: str
    thought: str
    tool_called: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Dict[str, Any]] = None

def append_traces(existing: List[AgentThought], new: List[AgentThought]) -> List[AgentThought]:
    """Custom reducer for LangGraph to append agent thoughts step-by-step."""
    return existing + new

class OmniResolveState(TypedDict):
    """Master LangGraph State passed across all nodes in the graph."""
    ticket_id: str
    customer_id: Optional[str]
    order_id: Optional[str]
    customer_message: str
    image_url: Optional[str]
    
    # Intent & Routing
    detected_intent: IntentType
    confidence: float
    intent_reasoning: str
    
    # Execution & Risk Assessment
    current_action: Optional[ActionPlan]
    status: TicketStatus
    human_feedback: Optional[str]
    
    # State Reducer: Every agent appending to agent_trace automatically accumulates
    agent_trace: Annotated[List[AgentThought], append_traces]
    
    # Output to customer
    final_response: str
