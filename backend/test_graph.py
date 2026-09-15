import asyncio
import uuid
from backend.agents.graph import omni_agent_graph
from backend.core.state import TicketStatus

async def run_tests():
    print("=" * 60)
    print("TEST 1: Autonomous Address Update (Order in PROCESSING)")
    print("=" * 60)
    state_1 = {
        "ticket_id": f"TCK-{uuid.uuid4().hex[:6]}",
        "customer_message": "Please update my shipping address for ORD-902 to 999 Tech Blvd, San Francisco, CA",
        "order_id": None,
        "image_url": None,
        "status": TicketStatus.PROCESSING,
        "agent_trace": []
    }
    result_1 = await omni_agent_graph.ainvoke(state_1)
    print("Final Status:", result_1["status"])
    print("Response:", result_1["final_response"])
    print("Thoughts Trace:")
    for t in result_1["agent_trace"]:
        print(f"  [{t.agent}]: {t.thought}")
        
    print("\n" + "=" * 60)
    print("TEST 2: High-Value Refund ($349.99) -> Requires HITL Approval")
    print("=" * 60)
    state_2 = {
        "ticket_id": f"TCK-{uuid.uuid4().hex[:6]}",
        "customer_message": "My headphones arrived damaged for ORD-901, I want a full refund!",
        "order_id": None,
        "image_url": "https://example.com/damaged_headphones.jpg",
        "status": TicketStatus.PROCESSING,
        "agent_trace": []
    }
    result_2 = await omni_agent_graph.ainvoke(state_2)
    print("Final Status:", result_2["status"])
    print("Response:", result_2["final_response"])
    print("Thoughts Trace:")
    for t in result_2["agent_trace"]:
        print(f"  [{t.agent}]: {t.thought}")

if __name__ == "__main__":
    asyncio.run(run_tests())
