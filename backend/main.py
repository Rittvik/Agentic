import uuid
import os
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.agents.graph import omni_agent_graph
from backend.core.state import OmniResolveState, TicketStatus
from backend.database.db import get_connection, init_db
from backend.tools.db_tools import update_shipping_address, process_refund
from backend.tools.n8n_tools import dispatch_resolution_to_n8n
app = FastAPI(title="OmniResolve Agentic Operations API", version="1.0.0")
# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Mount static frontend files & root index
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
# In-memory session store for live tickets
TICKETS_DB: Dict[str, OmniResolveState] = {}
# Ensure database is initialized on startup
@app.on_event("startup")
def on_startup():
    init_db()

class CustomerQueryRequest(BaseModel):
    message: str
    order_id: Optional[str] = None
    image_url: Optional[str] = None

class SupervisorApprovalRequest(BaseModel):
    decision: str # "APPROVE" or "REJECT"
    supervisor_notes: Optional[str] = "Approved by supervisor via n8n"

@app.post("/api/chat")
async def chat_with_agent(req: CustomerQueryRequest):
    """Customer chat endpoint: processes message through LangGraph Multi-Agent squad."""
    ticket_id = f"TCK-{uuid.uuid4().hex[:6].upper()}"
    
    initial_state: OmniResolveState = {
        "ticket_id": ticket_id,
        "customer_id": None,
        "order_id": req.order_id,
        "customer_message": req.message,
        "image_url": req.image_url,
        "status": TicketStatus.PROCESSING,
        "agent_trace": [],
        "detected_intent": None,
        "confidence": 0.0,
        "intent_reasoning": "",
        "current_action": None,
        "human_feedback": None,
        "final_response": ""
    }
    
    result_state = await omni_agent_graph.ainvoke(initial_state)
    TICKETS_DB[ticket_id] = result_state
    
    return {
        "ticket_id": ticket_id,
        "status": result_state["status"],
        "response": result_state["final_response"],
        "trace": result_state["agent_trace"]
    }

@app.post("/api/tickets/{ticket_id}/approve")
async def handle_human_approval(ticket_id: str, req: SupervisorApprovalRequest):
    """
    HITL Resume Endpoint: Called by n8n when a supervisor clicks 'Approve' or 'Reject'.
    """
    state = TICKETS_DB.get(ticket_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found.")
    
    if state["status"] != TicketStatus.PENDING_HUMAN_APPROVAL:
        return {"message": f"Ticket {ticket_id} is already in '{state['status']}' state."}
    
    action = state.get("current_action")
    if not action:
        raise HTTPException(status_code=400, detail="No pending action on this ticket.")
    
    if req.decision.upper() == "APPROVE":
        state["status"] = TicketStatus.APPROVED
        state["human_feedback"] = req.supervisor_notes
        
        # Execute the approved tool
        if action.action_type == "PROCESS_REFUND":
            result = process_refund(
                order_id=action.parameters["order_id"],
                amount=action.parameters["amount"],
                reason=f"Approved by supervisor: {req.supervisor_notes}"
            )
            state["final_response"] = f"Your refund claim of ${action.parameters['amount']:.2f} has been approved by our operations manager and processed (Txn: {result.get('transaction_id')})."
        elif action.action_type == "UPDATE_ADDRESS":
            result = update_shipping_address(
                order_id=action.parameters["order_id"],
                new_address=action.parameters["new_address"]
            )
            state["final_response"] = f"Address update approved by manager: changed to {action.parameters['new_address']}."
            
        state["status"] = TicketStatus.RESOLVED
        
        # Dispatch completion event to n8n
        await dispatch_resolution_to_n8n(
            ticket_id=ticket_id,
            summary=state["final_response"],
            resolution_details={"decision": "APPROVED", "notes": req.supervisor_notes}
        )
    else:
        state["status"] = TicketStatus.REJECTED
        state["human_feedback"] = req.supervisor_notes
        state["final_response"] = f"Your request was reviewed by our operations supervisor and could not be approved. Reason: {req.supervisor_notes}"
    
    TICKETS_DB[ticket_id] = state
    return {
        "ticket_id": ticket_id,
        "status": state["status"],
        "final_response": state["final_response"]
    }

@app.get("/api/tickets")
def get_all_tickets():
    """Returns all active and resolved tickets for the Operations Dashboard."""
    return list(TICKETS_DB.values())

@app.get("/api/database/inspect")
def inspect_database():
    """Returns database tables for live dashboard visualization."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    orders = [dict(row) for row in cursor.fetchall()]
    cursor.execute("SELECT * FROM customers")
    customers = [dict(row) for row in cursor.fetchall()]
    cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 10")
    txns = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"orders": orders, "customers": customers, "transactions": txns}
