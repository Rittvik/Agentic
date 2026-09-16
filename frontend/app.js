const API_BASE = 'http://localhost:8000';

function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));

    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');

    if (tabId === 'ops-tab') {
        loadTickets();
    } else if (tabId === 'db-tab') {
        loadDatabase();
    }
}

async function handleCustomerSubmit(event) {
    event.preventDefault();
    const input = document.getElementById('user-input');
    const orderInput = document.getElementById('order-id-input');
    const imageInput = document.getElementById('image-url-input');

    const message = input.value.trim();
    const order_id = orderInput.value.trim() || null;
    const image_url = imageInput.value.trim() || null;

    if (!message) return;

    // Append User message to chat
    appendMessage('user', '👤', message);
    input.value = '';

    // Append thinking bubble
    const thinkingId = appendMessage('bot', '🤖', '<em>OmniResolve is routing your inquiry through multi-agent graph...</em>');

    try {
        const res = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, order_id, image_url })
        });

        const data = await res.json();

        // Remove thinking message
        document.getElementById(thinkingId)?.remove();

        // Display bot response
        appendMessage('bot', '🤖', data.response);

        // Update live trace
        updateReasoningTrace(data.ticket_id, data.trace);
        loadTickets();

    } catch (err) {
        document.getElementById(thinkingId)?.remove();
        appendMessage('bot', '⚠️', `Error connecting to backend: ${err.message}`);
    }
}

function appendMessage(role, avatar, content) {
    const container = document.getElementById('chat-messages');
    const id = 'msg-' + Math.random().toString(36).substr(2, 9);

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    msgDiv.id = id;
    msgDiv.innerHTML = `
    <div class="avatar">${avatar}</div>
    <div class="bubble">${content}</div>
  `;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
    return id;
}

function resetChat() {
    document.getElementById('chat-messages').innerHTML = `
    <div class="message bot">
      <div class="avatar">🤖</div>
      <div class="bubble">
        Hello! I am OmniResolve, an autonomous operations agent. How can I help you today?
      </div>
    </div>
  `;
}

function updateReasoningTrace(ticketId, trace) {
    document.getElementById('active-ticket-id').innerText = ticketId;
    const traceFeed = document.getElementById('reasoning-trace');

    if (!trace || trace.length === 0) {
        traceFeed.innerHTML = '<p class="empty-state">No trace steps recorded.</p>';
        return;
    }

    traceFeed.innerHTML = trace.map(t => `
    <div class="trace-step">
      <div class="trace-agent">⚡ Step ${t.step}: ${t.agent}</div>
      <div class="trace-thought">${t.thought}</div>
      ${t.tool_called ? `<div style="color: #38bdf8; font-family: monospace; font-size: 0.75rem; margin-top: 4px;">🔧 Tool: ${t.tool_called}</div>` : ''}
    </div>
  `).join('');
}

async function loadTickets() {
    try {
        const res = await fetch(`${API_BASE}/api/tickets`);
        const tickets = await res.json();

        const pending = tickets.filter(t => t.status === 'PENDING_HUMAN_APPROVAL');
        document.getElementById('pending-badge').innerText = pending.length;

        const queueList = document.getElementById('hitl-queue');
        if (pending.length === 0) {
            queueList.innerHTML = '<p class="empty-state">No pending manager approvals in queue.</p>';
            return;
        }

        queueList.innerHTML = pending.map(t => `
      <div class="hitl-item">
        <div class="hitl-header">
          <span>Ticket: ${t.ticket_id}</span>
          <span>Risk: ${t.current_action?.risk_level || 'HIGH'}</span>
        </div>
        <p style="font-size: 0.85rem; color: #f3f4f6;"><strong>Inquiry:</strong> "${t.customer_message}"</p>
        <p style="font-size: 0.8rem; color: #94a3b8;"><strong>Reason:</strong> ${t.current_action?.risk_reasoning || 'Exceeds auto-limit'}</p>
        <div class="hitl-actions">
          <button class="btn-success" onclick="approveTicket('${t.ticket_id}', 'APPROVE')">✓ Approve Action</button>
          <button class="btn-danger" onclick="approveTicket('${t.ticket_id}', 'REJECT')">✕ Reject Claim</button>
        </div>
      </div>
    `).join('');

    } catch (err) {
        console.error("Error loading tickets:", err);
    }
}

async function approveTicket(ticketId, decision) {
    try {
        const res = await fetch(`${API_BASE}/api/tickets/${ticketId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ decision, supervisor_notes: `Decision '${decision}' executed from Ops Command Center.` })
        });

        const data = await res.json();
        alert(`Ticket ${ticketId} status: ${data.status}`);
        loadTickets();
        loadDatabase();
    } catch (err) {
        alert(`Error: ${err.message}`);
    }
}

async function loadDatabase() {
    try {
        const res = await fetch(`${API_BASE}/api/database/inspect`);
        const data = await res.json();

        // Orders table
        const ordersTbody = document.querySelector('#orders-table tbody');
        ordersTbody.innerHTML = data.orders.map(o => `
      <tr>
        <td><code>${o.order_id}</code></td>
        <td>${o.customer_id}</td>
        <td>${o.item_name}</td>
        <td>$${o.amount.toFixed(2)}</td>
        <td><span class="tag ${o.status === 'REFUNDED' ? 'high' : 'low'}">${o.status}</span></td>
        <td>${o.shipping_address}</td>
      </tr>
    `).join('');

        // Transactions table
        const txnsTbody = document.querySelector('#txns-table tbody');
        txnsTbody.innerHTML = data.transactions.map(t => `
      <tr>
        <td><code>${t.transaction_id}</code></td>
        <td>${t.order_id}</td>
        <td><strong>${t.type}</strong></td>
        <td>$${t.amount ? t.amount.toFixed(2) : '0.00'}</td>
        <td><span class="tag low">${t.status}</span></td>
        <td>${t.details}</td>
      </tr>
    `).join('');

    } catch (err) {
        console.error("Error inspecting DB:", err);
    }
}

function runScenario(type) {
    switchTab('customer-tab');

    if (type === 'address_processing') {
        document.getElementById('user-input').value = 'Please change my shipping address for ORD-902 to 777 Innovation Way, Seattle, WA';
        document.getElementById('order-id-input').value = 'ORD-902';
    } else if (type === 'refund_hitl') {
        document.getElementById('user-input').value = 'My Sony Headphones arrived broken in the mail for ORD-901, I want a full refund!';
        document.getElementById('order-id-input').value = 'ORD-901';
        document.getElementById('image-url-input').value = 'https://example.com/damaged_headphones.png';
    } else if (type === 'address_shipped_block') {
        document.getElementById('user-input').value = 'I moved, please change the address for ORD-903 to Miami, FL';
        document.getElementById('order-id-input').value = 'ORD-903';
    } else if (type === 'order_tracking') {
        document.getElementById('user-input').value = 'Where is my order ORD-901 right now?';
        document.getElementById('order-id-input').value = 'ORD-901';
    }
}

// Initial load
loadDatabase();
setInterval(loadTickets, 5000);
