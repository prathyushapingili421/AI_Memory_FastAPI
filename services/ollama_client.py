import httpx
import json
from typing import List, Dict

from ..config import settings

class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.chat_model = settings.CHAT_MODEL
        self.embed_model = settings.EMBED_MODEL
        self.client = httpx.AsyncClient()

    async def chat_completion(self, messages: List[Dict]) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.chat_model,
            "messages": messages,
            "stream": False
        }
        try:
            response = await self.client.post(url, json=payload, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
        except httpx.HTTPStatusError as e:
            print(f"HTTP error during chat completion: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Error during chat completion: {e}")
            raise

    async def generate_embedding(self, text: str) -> List[float]:
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.embed_model,
            "prompt": text
        }
        try:
            response = await self.client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            return data["embedding"]
        except httpx.HTTPStatusError as e:
            print(f"HTTP error during embedding generation: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Error during embedding generation: {e}")
            raise

ollama_client = OllamaClient()