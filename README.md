# OmniResolve: Autonomous Support & Action Resolution Engine with Human-in-the-Loop (HITL)

**OmniResolve** is an enterprise-grade customer operations and autonomous resolution platform. It demonstrates the seamless fusion of **Multi-Agent AI (LangGraph)**, **Structured LLM API Integration (Google Gemini / OpenAI)**, and **n8n Workflow Automation**.

---

## 🏛️ Architecture Overview

```
                                  +-----------------------------+
                                  |     Omnichannel Ingestion   |
                                  | (Web Chat / Email / Webhook)|
                                  +--------------+--------------+
                                                 |
                                                 v
                                  +-----------------------------+
                                  |   n8n Workflow Engine       |
                                  | - Webhook Ingestion         |
                                  | - Payload Pre-processing    |
                                  +--------------+--------------+
                                                 |
                                                 v
                                  +-----------------------------+
                                  |  OmniResolve Agent API      |
                                  |        (FastAPI)            |
                                  +--------------+--------------+
                                                 |
                                                 v
                                  +-----------------------------+
                                  |     Supervisor Agent        |
                                  | - Intent Classification     |
                                  | - Parameter Extraction      |
                                  +--------------+--------------+
                                                 |
                       +-------------------------+-------------------------+
                       |                                                   |
                       v                                                   v
        +-------------------------------+                   +-------------------------------+
        |    Logistics & Orders Agent   |                   |     Billing & Refund Agent    |
        | - Order Tracking Check        |                   | - Damage Claim Assessment     |
        | - Shipping Address Update     |                   | - Refund Amount Calculation   |
        +---------------+---------------+                   +---------------+---------------+
                        |                                                   |
                        +------------------------+--------------------------+
                                                 |
                                                 v
                                  +-----------------------------+
                                  |  Guardrail & Policy Agent   |
                                  | - Strict Policy Evaluation  |
                                  | - $50 Auto-Refund Limit     |
                                  | - Risk: LOW / HIGH (HITL)   |
                                  +--------------+--------------+
                                                 |
                                                 v
                                      +-----------------------+
                                      | Is High Risk / HITL?  |
                                      +-----------+-----------+
                                     NO /         \ YES
                                       /           \
                                      v             v
                       +-------------------+   +------------------------------------+
                       | Execute Tool &    |   | State: PENDING_HUMAN_APPROVAL      |
                       | Complete Action   |   | -> Emits Webhook to n8n            |
                       +---------+---------+   +-----------------+------------------+
                                 |                               |
                                 |                               v
                                 |             +------------------------------------+
                                 |             | n8n Human-in-the-Loop Workflow     |
                                 |             | - Interactive Manager Alert Card   |
                                 |             | - Supervisor clicks [Approve/Deny] |
                                 |             +-----------------+------------------+
                                 |                               |
                                 |                               v
                                 |             +------------------------------------+
                                 |             | Resume Agent Callback Endpoint     |
                                 |             +-----------------+------------------+
                                 |                               |
                                 +---------------+---------------+
                                                 |
                                                 v
                                  +-----------------------------+
                                  | n8n Post-Resolution Workflow|
                                  | - Syncs to CRM / DB Logs    |
                                  | - Sends Resolution Receipt  |
                                  +-----------------------------+
```

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.12 / 3.14)
- **Node.js v18+** (for running `n8n` locally via `npx`) OR **Docker**

---

### 2. Virtual Environment Setup & Dependencies

In your project root (`/Users/rittvikvashishtha/Agentic`):

```bash
# 1. Create the virtual environment
python3 -m venv venv

# 2. Activate the virtual environment
# On macOS / Linux:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\activate

# 3. Install required Python packages
pip install -r requirements.txt
```

---

### 3. Configure Environment Variables & API Keys

Set your preferred LLM API keys in your environment or configure them directly in `backend/core/config.py`:

```bash
# Optional: export directly in terminal
export GEMINI_API_KEY="your-gemini-api-key-here"
export DEFAULT_PROVIDER="gemini" # or "openai"
```

*(Note: The system includes a smart fallback mechanism, allowing test runs and demo simulations even offline without an API key).*

---

### 4. Running the Workflow Automation Engine (n8n)

Start the local n8n workflow server in a separate terminal:

#### Method A: Using `npx` (No Docker required)
```bash
npx n8n
```
- Open your browser to [http://localhost:5678](http://localhost:5678).
- Complete the initial 1-time setup.
- Webhooks will be active on `http://localhost:5678/webhook/...`.

#### Method B: Using Docker
```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n
```

---

### 5. Running the FastAPI Agentic Backend with Uvicorn

In your active virtual environment terminal:

```bash
# 1. Initialize SQLite mock e-commerce database (if not already created)
python -m backend.database.db

# 2. Start the Uvicorn server
uvicorn backend.main:app --reload --port 8000
```

- **Interactive Swagger API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Redoc Docs:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### 6. Testing the Multi-Agent System (CLI Test Runner)

To test the LangGraph multi-agent decision loop from the command line:

```bash
python -m backend.test_graph
```

This executes two built-in benchmark scenarios:
1. **Low-Risk Scenario**: Address update on a processing order $\rightarrow$ Evaluated by Guardrail $\rightarrow$ Autonomously executed in DB $\rightarrow$ `RESOLVED`.
2. **High-Risk Scenario**: $349.99 damage claim refund $\rightarrow$ Exceeds $50 auto-refund threshold $\rightarrow$ State paused at `PENDING_HUMAN_APPROVAL` $\rightarrow$ Dispatches HITL alert to n8n.

---

## 📡 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Customer chat endpoint; passes inquiry through LangGraph agents |
| `POST` | `/api/tickets/{ticket_id}/approve` | HITL Resume Endpoint called by n8n / supervisor upon human decision |
| `GET` | `/api/tickets` | Returns all active and resolved ticket states and reasoning traces |
| `GET` | `/api/database/inspect` | Returns live SQLite tables (Orders, Customers, Transactions) |

---

## 🔄 n8n Workflows Included

Import these pre-built workflow JSONs from the `n8n_workflows/` directory into your n8n canvas:

1. **`01_omnichannel_ticket_intake.json`**:
   - Webhook trigger on `/webhook/ticket-intake`.
   - Dispatches payload to OmniResolve agent at `http://localhost:8000/api/chat`.
2. **`02_human_in_the_loop_approval.json`**:
   - Webhook trigger on `/webhook/hitl-approval`.
   - Formats manager alert card and executes approval callback to `POST /api/tickets/{ticket_id}/approve`.
3. **`03_post_resolution_crm_sync.json`**:
   - Webhook trigger on `/webhook/ticket-resolved`.
   - Formats resolution audit logs for CRM / Google Sheets sync.

---

## 💡 Key Portfolio & Interview Talking Points

1. **Multi-Agent Orchestration with LangGraph**:
   - Modular separation of concerns between Supervisor (routing), Domain Specialists (Billing & Logistics), and Safety Guardrails.
   - Stateful memory tracking with custom reducers for full auditability.
2. **Deterministic Safety Guardrails**:
   - AI proposes actions, but deterministic policy engines enforce critical thresholds (e.g. monetary limits, order state validity).
3. **Human-in-the-Loop (HITL) State Machine**:
   - Non-blocking async suspension of workflows awaiting managerial sign-off via webhooks.
4. **Production Webhook Integration with n8n**:
   - Bridges modern LLM reasoning agents with enterprise tools (Slack, Email, CRMs, Databases).
