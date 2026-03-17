import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration - change once, use everywhere"""

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your-key-here")
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
            print("Warning: GROQ_API_KEY not set in .env. Falling back to local rule-based analysis.")
        return True
