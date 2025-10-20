from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from ..config import settings
from ..models import Message, Summary, Episode
from typing import List, Optional
import numpy as np

class MongoManager:
    client: AsyncIOMotorClient = None
    db = None

    # ------------------------------------------------------------------
    # Connection Management
    # ------------------------------------------------------------------
    async def connect_to_mongo(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.db = self.client[settings.DB_NAME]
        print(f"Connected to MongoDB: {settings.DB_NAME}")

        # Ensure indexes for efficient querying
        await self.db.messages.create_index([
            ("user_id", ASCENDING),
            ("session_id", ASCENDING),
            ("created_at", DESCENDING)
        ])
        await self.db.summaries.create_index([
            ("user_id", ASCENDING),
            ("session_id", ASCENDING),
            ("scope", ASCENDING),
            ("created_at", DESCENDING)
        ])
        await self.db.episodes.create_index([
            ("user_id", ASCENDING),
            ("session_id", ASCENDING),
            ("created_at", DESCENDING)
        ])

    async def close_mongo_connection(self):
        self.client.close()
        print("MongoDB connection closed.")

    # ------------------------------------------------------------------
    # Message Operations
    # ------------------------------------------------------------------
    async def save_message(self, message: Message):
        await self.db.messages.insert_one(message.model_dump())

    async def get_last_n_messages(self, user_id: str, session_id: Optional[str], n: int) -> List[Message]:
        query = {"user_id": user_id}
        if session_id:
            query["session_id"] = session_id
        
        cursor = self.db.messages.find(query).sort("created_at", DESCENDING).limit(n)
        return [Message(**doc) async for doc in cursor]

    async def count_user_messages_in_session(self, user_id: str, session_id: str) -> int:
        return await self.db.messages.count_documents({
            "user_id": user_id,
            "session_id": session_id,
            "role": "user"
        })

    # ------------------------------------------------------------------
    # Summary Operations
    # ------------------------------------------------------------------
    async def upsert_summary(self, summary: Summary):
        query = {"user_id": summary.user_id, "scope": summary.scope}
        if summary.session_id:
            query["session_id"] = summary.session_id
        
        await self.db.summaries.update_one(
            query,
            {"$set": summary.model_dump()},
            upsert=True
        )

    async def get_latest_summary(self, user_id: str, scope: str, session_id: Optional[str] = None) -> Optional[Summary]:
        query = {"user_id": user_id, "scope": scope}
        if scope == "session" and session_id:
            query["session_id"] = session_id
        elif scope == "user":  # Lifetime summary has null session_id
            query["session_id"] = None
        
        doc = await self.db.summaries.find_one(query, sort=[("created_at", DESCENDING)])
        return Summary(**doc) if doc else None

    async def get_all_session_summaries(self, user_id: str) -> List[Summary]:
        cursor = self.db.summaries.find({"user_id": user_id, "scope": "session"}).sort("created_at", DESCENDING)
        return [Summary(**doc) async for doc in cursor]

    # ------------------------------------------------------------------
    # Episode Operations
    # ------------------------------------------------------------------
    async def save_episode(self, episode: Episode):
        await self.db.episodes.insert_one(episode.model_dump())

    async def get_top_k_episodes_by_similarity(self, user_id: str, embedding: List[float], k: int) -> List[Episode]:
        """
        Retrieves the top-k most similar episodic memories for a given user.
        Skips any episode whose embedding dimension doesn't match the query vector.
        """
        cursor = self.db.episodes.find({"user_id": user_id})
        all_episodes = [Episode(**doc) async for doc in cursor]

        if not all_episodes:
            print(f"[DEBUG] No episodes found for user {user_id}")
            return []

        query_vec = np.array(embedding, dtype=np.float32)
        query_dim = len(query_vec)
        similarities = []

        for episode in all_episodes:
            episode_vec = np.array(episode.embedding, dtype=np.float32)
            ep_dim = len(episode_vec)

            # --- Dimension mismatch guard ---
            if ep_dim != query_dim:
                print(f"[WARN] Skipping episode (dim mismatch): query={query_dim}, episode={ep_dim}")
                continue

            # --- Safe cosine similarity computation ---
            try:
                denom = (np.linalg.norm(query_vec) * np.linalg.norm(episode_vec)) + 1e-10
                similarity = float(np.dot(query_vec, episode_vec) / denom)
                similarities.append((similarity, episode))
            except Exception as e:
                print(f"[ERROR] Similarity computation failed for episode {getattr(episode, 'id', None)}: {e}")
                continue

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[0], reverse=True)
        top_k = [ep for sim, ep in similarities[:k]]

        print(f"[DEBUG] Retrieved {len(top_k)} episodic facts for user={user_id} (from {len(all_episodes)} total)")
        return top_k

    async def get_last_n_episodic_facts(self, user_id: str, n: int) -> List[str]:
        cursor = self.db.episodes.find({"user_id": user_id}).sort("created_at", DESCENDING).limit(n)
        return [doc["fact"] async for doc in cursor]


# ------------------------------------------------------------------
# Create a global instance for imports
# ------------------------------------------------------------------
mongo_manager = MongoManager()
