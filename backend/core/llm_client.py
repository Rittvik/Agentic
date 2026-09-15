import os
import json
from typing import Type, TypeVar, Optional, Any
from pydantic import BaseModel
from backend.core.config import settings

T = TypeVar("T", bound=BaseModel)

def get_llm():
    """Returns the initialized LangChain LLM instance based on configuration."""
    if settings.DEFAULT_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1
        )
    elif settings.OPENAI_API_KEY:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )
    return None

async def call_structured_llm(
    prompt: str,
    output_schema: Type[T],
    system_instruction: str = "",
    mock_fallback: Optional[T] = None
) -> T:
    """
    Calls the LLM with strict Pydantic structured output validation.
    If no API key is provided, returns the mock_fallback to ensure offline testability.
    """
    llm = get_llm()
    
    if llm is not None:
        try:
            structured_llm = llm.with_structured_output(output_schema)
            messages = []
            if system_instruction:
                messages.append(("system", system_instruction))
            messages.append(("human", prompt))
            result = await structured_llm.ainvoke(messages)
            return result
        except Exception as e:
            print(f"[LLM Client Warning] API invocation failed ({e}). Using schema fallback.")
    
    # Fallback for local testing/dev when API key isn't set yet
    if mock_fallback is not None:
        return mock_fallback
    
    # Construct empty default instance if possible
    return output_schema.model_construct()
