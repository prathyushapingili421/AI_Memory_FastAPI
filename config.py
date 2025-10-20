import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str
    DB_NAME: str
    OLLAMA_BASE_URL: str
    CHAT_MODEL: str
    EMBED_MODEL: str
    SHORT_TERM_N: int
    SUMMARIZE_EVERY_USER_MSGS: int
    EPISODE_EXTRACTION_LIMIT: int
    EPISODE_RETRIEVAL_K: int

    class Config:
        # Construct the absolute path to the .env file
        # This assumes .env is always in the same directory as config.py
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        # If .env is in the project root (AI_MEMORY_FASTAPI/):
        # env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        # No, wait, if config.py is in AI_MEMORY_FASTAPI, and .env is in AI_MEMORY_FASTAPI as well.
        # then this will work:
        # env_file = ".env"
        # However, because you are running from the parent, the CWD is /Users/spartan/Documents/
        # So we need to point to /Users/spartan/Documents/ai_memory_fastapi/.env
        
        # Let's be explicit and robust:
        # This calculates the path from where config.py is located.
        # __file__ is /Users/spartan/Documents/ai_memory_fastapi/config.py
        # os.path.dirname(__file__) is /Users/spartan/Documents/ai_memory_fastapi/
        # os.path.join(..., ".env") becomes /Users/spartan/Documents/ai_memory_fastapi/.env
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

settings = Settings()