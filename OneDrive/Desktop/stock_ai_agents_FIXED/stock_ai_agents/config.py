import os

from dotenv import load_dotenv

load_dotenv()


def _load_groq_api_key() -> str:
    env_key = os.getenv("GROQ_API_KEY")
    if env_key:
        return env_key

    try:
        import streamlit as st

        secret_key = st.secrets.get("GROQ_API_KEY")
        if secret_key:
            return secret_key
    except Exception:
        pass

    return "your-key-here"


class Config:
    """Central configuration - change once, use everywhere"""

    GROQ_API_KEY = _load_groq_api_key()
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

    MODELS = {
        "fast": "llama-3.1-8b-instant",
        "smart": "llama-3.3-70b-versatile",
    }

    MAX_RETRIES = 3
    RETRY_DELAY = 2
    REQUESTS_PER_MINUTE = 30

    @classmethod
    def has_groq_key(cls) -> bool:
        return bool(cls.GROQ_API_KEY and cls.GROQ_API_KEY != "your-key-here")

    @classmethod
    def validate(cls) -> bool:
        if not cls.has_groq_key():
            print("Warning: GROQ_API_KEY not set. Falling back to local rule-based analysis.")
        return True
