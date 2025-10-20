from typing import List
from .ollama_client import ollama_client

async def generate_embedding(text: str) -> List[float]:
    """
    Generates an embedding using the Ollama embedding model.
    Should return a 768-dimensional vector (default for models like 'nomic-embed-text').
    """
    embedding = await ollama_client.generate_embedding(text)
    print(f"[DEBUG] Generated embedding length: {len(embedding)}")
    return embedding

    # --- Real embedding from Ollama ---
    try:
        embedding = await ollama_client.generate_embedding(text)
        print(f"[DEBUG] Generated real embedding (len={len(embedding)}) for text: {text[:50]}...")
        return embedding
    except Exception as e:
        print(f"[ERROR] Failed to generate embedding: {e}")
        # Return a fallback dummy embedding to prevent crashes
        return [0.0] * 10
