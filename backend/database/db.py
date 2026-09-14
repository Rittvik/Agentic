import sqlite3
import os
from typing import Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "omni_resolve.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite schema with mock e-commerce data."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Customers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        vip_status BOOLEAN DEFAULT 0,
        trust_score REAL DEFAULT 0.95
    );
    """)
    
    # Orders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        item_name TEXT NOT NULL,
        amount REAL NOT NULL,
        status TEXT NOT NULL, -- 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'REFUNDED'
        shipping_address TEXT NOT NULL,
        order_date TEXT NOT NULL,
        tracking_number TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
    );
    """)
    
    # Audit / Transactions Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        type TEXT NOT NULL, -- 'PAYMENT', 'REFUND', 'STORE_CREDIT', 'ADDRESS_CHANGE'
        amount REAL,
        status TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        details TEXT
    );
    """)
    
    # Seed sample mock data if empty
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO customers VALUES ('CUST-101', 'Alice Johnson', 'alice@example.com', 1, 0.98)")
        cursor.execute("INSERT INTO customers VALUES ('CUST-102', 'Bob Smith', 'bob@example.com', 0, 0.75)")
        cursor.execute("INSERT INTO customers VALUES ('CUST-103', 'Charlie Brown', 'charlie@example.com', 0, 0.40)")
        
        # Order 1: Delivered (Eligible for damage claim/refund)
        cursor.execute("INSERT INTO orders VALUES ('ORD-901', 'CUST-101', 'Sony WH-1000XM5 Headphones', 349.99, 'DELIVERED', '742 Evergreen Terrace, Springfield', '2026-09-01', 'TRK-987654')")
        # Order 2: Processing (Eligible for address change or cancellation)
        cursor.execute("INSERT INTO orders VALUES ('ORD-902', 'CUST-102', 'Logitech MX Master 3S Mouse', 99.99, 'PROCESSING', '123 Main St, Austin, TX', '2026-09-13', NULL)")
        # Order 3: Shipped (Address change blocked by policy without reroute)
        cursor.execute("INSERT INTO orders VALUES ('ORD-903', 'CUST-103', 'Mechanical Keyboard RGB', 149.99, 'SHIPPED', '456 Elm St, Seattle, WA', '2026-09-10', 'TRK-112233')")
        
        conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at", DB_PATH)
