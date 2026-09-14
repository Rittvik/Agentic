import httpx
from typing import Dict, Any
from backend.core.config import settings

async def dispatch_hitl_to_n8n(ticket_id: str, action_plan: Dict[str, Any], customer_message: str, customer_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dispatches a high-risk action request to n8n to send an interactive Slack/Email approval card.
    """
    payload = {
        "event": "HUMAN_APPROVAL_REQUIRED",
        "ticket_id": ticket_id,
        "action_plan": action_plan,
        "customer_message": customer_message,
        "customer_info": customer_info,
        "approval_callback_url": f"http://localhost:8000/api/tickets/{ticket_id}/approve"
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(settings.N8N_HITL_WEBHOOK_URL, json=payload)
            return {"status": "DISPATCHED", "n8n_status_code": response.status_code}
    except Exception as e:
        # If n8n is not running locally during testing, return mock acknowledgement
        return {"status": "DISPATCHED_OFFLINE_MOCK", "details": str(e)}

async def dispatch_resolution_to_n8n(ticket_id: str, summary: str, resolution_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dispatches ticket completion data to n8n to sync to CRM/Google Sheets and email the customer.
    """
    payload = {
        "event": "TICKET_RESOLVED",
        "ticket_id": ticket_id,
        "summary": summary,
        "resolution_details": resolution_details
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(settings.N8N_SYNC_WEBHOOK_URL, json=payload)
            return {"status": "SYNCED", "n8n_status_code": response.status_code}
    except Exception as e:
        return {"status": "SYNCED_OFFLINE_MOCK", "details": str(e)}
