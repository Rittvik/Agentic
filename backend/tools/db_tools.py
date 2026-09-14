import uuid
from typing import Dict, Any, Optional
from backend.database.db import get_connection

def lookup_order(order_id: str) -> Optional[Dict[str, Any]]:
    """Fetches order details by Order ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.*, c.name as customer_name, c.email as customer_email, c.vip_status, c.trust_score 
        FROM orders o 
        JOIN customers c ON o.customer_id = c.customer_id 
        WHERE o.order_id = ?
    """, (order_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def update_shipping_address(order_id: str, new_address: str) -> Dict[str, Any]:
    """Updates shipping address if the order is still in PROCESSING status."""
    order = lookup_order(order_id)
    if not order:
        return {"success": False, "error": f"Order {order_id} not found."}
    
    if order["status"] != "PROCESSING":
        return {
            "success": False, 
            "error": f"Cannot update address. Order is already '{order['status']}'. Policy requires orders to be in 'PROCESSING' state."
        }
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET shipping_address = ? WHERE order_id = ?", (new_address, order_id))
    
    # Log transaction
    txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    cursor.execute("""
        INSERT INTO transactions (transaction_id, order_id, type, amount, status, details)
        VALUES (?, ?, 'ADDRESS_CHANGE', 0, 'COMPLETED', ?)
    """, (txn_id, order_id, f"Address changed from '{order['shipping_address']}' to '{new_address}'"))
    
    conn.commit()
    conn.close()
    return {"success": True, "transaction_id": txn_id, "new_address": new_address}

def process_refund(order_id: str, amount: float, reason: str) -> Dict[str, Any]:
    """Executes a refund on an order and marks it in the database."""
    order = lookup_order(order_id)
    if not order:
        return {"success": False, "error": f"Order {order_id} not found."}
    
    if amount > order["amount"]:
        return {"success": False, "error": f"Refund amount (${amount}) exceeds order total (${order['amount']})."}
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'REFUNDED' WHERE order_id = ?", (order_id,))
    
    txn_id = f"RFND-{uuid.uuid4().hex[:8].upper()}"
    cursor.execute("""
        INSERT INTO transactions (transaction_id, order_id, type, amount, status, details)
        VALUES (?, ?, 'REFUND', ?, 'COMPLETED', ?)
    """, (txn_id, order_id, amount, reason))
    
    conn.commit()
    conn.close()
    return {
        "success": True, 
        "transaction_id": txn_id, 
        "amount_refunded": amount, 
        "order_id": order_id,
        "status": "REFUNDED"
    }
