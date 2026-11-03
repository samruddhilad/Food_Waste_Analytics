import os
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def get_configured_llm_info(custom_key: Optional[str] = None, provider_choice: Optional[str] = None) -> Tuple[str, bool]:
    """
    Checks which LLM provider is configured and returns (provider_name, is_active).
    """
    google_key = custom_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    openai_key = custom_key or os.getenv("OPENAI_API_KEY")

    if provider_choice == "Google Gemini" and google_key:
        return "Google Gemini", True
    elif provider_choice == "OpenAI" and openai_key:
        return "OpenAI", True
    elif google_key:
        return "Google Gemini", True
    elif openai_key:
        return "OpenAI", True
    else:
        return "Rule-Based Deterministic Engine (No API Key Configured)", False

def get_llm(custom_key: Optional[str] = None, provider_choice: Optional[str] = None):
    """
    Instantiates and returns the configured LangChain BaseChatModel or None.
    Handles graceful fallback without crashing.
    """
    google_key = (custom_key if provider_choice == "Google Gemini" else None) or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    openai_key = (custom_key if provider_choice == "OpenAI" else None) or os.getenv("OPENAI_API_KEY")

    # 1. Check Google Gemini
    if (provider_choice == "Google Gemini" or provider_choice is None) and google_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=google_key,
                temperature=0.2,
            )
        except Exception:
            try:
                # Fallback model
                from langchain_google_genai import ChatGoogleGenerativeAI
                return ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=google_key,
                    temperature=0.2,
                )
            except Exception as e:
                print(f"[LLM Factory] Error initializing Gemini: {e}")

    # 2. Check OpenAI
    if (provider_choice == "OpenAI" or provider_choice is None) and openai_key:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="gpt-4o-mini",
                api_key=openai_key,
                temperature=0.2,
            )
        except Exception as e:
            print(f"[LLM Factory] Error initializing OpenAI: {e}")

    # 3. If neither or initialization failed
    return None
