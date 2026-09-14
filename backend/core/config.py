import os
from pydantic import BaseModel

class Settings(BaseModel):
    # LLM Providers
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "AIzaSyBChwluMIs_MvDKMeFEdleagsYWAWHJDS4")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "gemini") # "gemini" or "openai"
    
    # n8n Webhook Endpoints (can be localhost:5678 or your cloud n8n)
    N8N_HITL_WEBHOOK_URL: str = os.getenv("N8N_HITL_WEBHOOK_URL", "http://localhost:5678/webhook/hitl-approval")
    N8N_SYNC_WEBHOOK_URL: str = os.getenv("N8N_SYNC_WEBHOOK_URL", "http://localhost:5678/webhook/ticket-resolved")
    
    # E-Commerce Policies
    AUTO_REFUND_LIMIT: float = 50.00  # Any refund over $50 triggers Human-in-the-Loop

settings = Settings()
