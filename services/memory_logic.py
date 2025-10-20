from typing import List, Dict, Optional
from datetime import datetime
from ..config import settings
from ..models import Message, Summary, Episode
from ..mongoimpl.mongo import mongo_manager
from .ollama_client import ollama_client
from .embeddings import generate_embedding
import json


async def compose_chat_prompt(
    user_id: str,
    session_id: Optional[str],
    current_message_content: str,
    short_term_messages: List[Message],
    latest_session_summary: Optional[Summary],
    latest_lifetime_summary: Optional[Summary],
    episodic_facts: List[str]
) -> List[Dict]:
    """Composes the prompt for the chat model."""
    
    messages = []

    # System primer
    system_primer = (
        "You are a helpful AI assistant. Respond concisely and accurately. "
        "Use the provided context to inform your answers, but do not directly quote it unless necessary."
    )
    messages.append({"role": "system", "content": system_primer})

    # Long-term summaries
    if latest_lifetime_summary:
        messages.append({"role": "system", "content": f"User's lifetime summary: {latest_lifetime_summary.text}"})
    if latest_session_summary:
        messages.append({"role": "system", "content": f"Current session summary: {latest_session_summary.text}"})

    # Episodic facts
    if episodic_facts:
        facts_str = "; ".join(episodic_facts)
        messages.append({"role": "system", "content": f"Relevant past experiences: {facts_str}"})

    # Short-term memory (reversed to be chronologically correct in prompt)
    for msg in reversed(short_term_messages):
        messages.append({"role": msg.role, "content": msg.content})

    # Current user message
    messages.append({"role": "user", "content": current_message_content})

    return messages


async def extract_and_store_episodes(user_id: str, session_id: Optional[str], user_message: str):
    """
    Extracts facts from a user message, embeds them, and stores them as episodes.
    This version safely handles malformed JSON and ensures only valid facts are stored.
    """
    prompt_for_facts = (
        f"Extract up to {settings.EPISODE_EXTRACTION_LIMIT} short, concise facts "
        "from the following user message that might be useful for future reference. "
        "Each fact should be a standalone statement. "
        "Rate their importance from 0.0 (least important) to 1.0 (most important). "
        "Format as a JSON list of objects with 'fact' (string) and 'importance' (float): "
        f"User message: '{user_message}'"
    )

    try:
        response_text = await ollama_client.chat_completion(
            messages=[{"role": "user", "content": prompt_for_facts}]
        )

        # Clean markdown if present (```json)
        cleaned_text = response_text.replace("```json", "").replace("```", "").strip()

        try:
            parsed = json.loads(cleaned_text)
            facts = [
                f for f in parsed
                if isinstance(f, dict) and "fact" in f and "importance" in f
            ]
            print(f"[DEBUG] Extracted valid facts: {facts}")
        except Exception as e:
            print(f"[WARN] Could not parse extracted facts: {e}\nRaw response:\n{response_text}")
            return

        for item in facts:
            fact_text = item.get("fact")
            importance = float(item.get("importance", 0.5))

            if not fact_text:
                continue

            embedding = await generate_embedding(fact_text)
            print(f"[DEBUG] Saving episode: '{fact_text}' | dim={len(embedding)} | importance={importance}")

            episode = Episode(
                user_id=user_id,
                session_id=session_id,
                fact=fact_text,
                importance=min(max(0.0, importance), 1.0),
                embedding=embedding,
                created_at=datetime.utcnow()
            )

            await mongo_manager.save_episode(episode)
            print(f"[DEBUG] ✅ Episode saved for user={user_id}")

    except Exception as e:
        print(f"[ERROR] Episode extraction or storage failed: {e}")


async def summarize_conversation(user_id: str, session_id: str, recent_messages: List[Message]) -> Optional[Summary]:
    """Generates a session summary from recent messages."""
    
    if not recent_messages:
        return None

    conversation_text = "\n".join([f"{msg.role}: {msg.content}" for msg in recent_messages])
    
    prompt = (
        "Condense the following conversation into a concise summary, "
        "highlighting key topics, decisions, or important information in bullet points. "
        "This summary will be used to remind an AI assistant about the session's context. "
        f"Conversation:\n{conversation_text}"
    )

    try:
        summary_text = await ollama_client.chat_completion(
            messages=[{"role": "user", "content": prompt}]
        )
        return Summary(
            user_id=user_id,
            session_id=session_id,
            scope="session",
            text=summary_text,
            created_at=datetime.utcnow()
        )
    except Exception as e:
        print(f"Error during session summarization: {e}")
        return None


async def refresh_lifetime_summary(user_id: str):
    """Refreshes the lifetime summary by condensing all session summaries."""
    session_summaries = await mongo_manager.get_all_session_summaries(user_id)
    if not session_summaries:
        return None

    summaries_text = "\n".join([f"- {s.text}" for s in session_summaries])
    
    prompt = (
        "Condense the following session summaries into a single, comprehensive lifetime profile "
        "for the user. Focus on recurring themes, user preferences, and significant information "
        "that defines the user's overall interaction. "
        f"Session Summaries:\n{summaries_text}"
    )
    try:
        lifetime_summary_text = await ollama_client.chat_completion(
            messages=[{"role": "user", "content": prompt}]
        )
        lifetime_summary = Summary(
            user_id=user_id,
            session_id=None,  # Null for lifetime
            scope="user",
            text=lifetime_summary_text,
            created_at=datetime.utcnow()
        )
        await mongo_manager.upsert_summary(lifetime_summary)
        return lifetime_summary
    except Exception as e:
        print(f"Error during lifetime summarization: {e}")
        return None
