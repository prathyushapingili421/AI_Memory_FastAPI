from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
import json  # Used for parsing fact extraction

from ..config import settings
from ..models import ChatRequest, ChatResponse, Message, Summary, Episode
from ..mongoimpl.mongo import mongo_manager
from ..services.ollama_client import ollama_client
from ..services.memory_logic import (
    compose_chat_prompt,
    extract_and_store_episodes,
    summarize_conversation,
    refresh_lifetime_summary
)
from ..services.embeddings import generate_embedding  # For episode retrieval

router = APIRouter()


@router.post("/", response_model=ChatResponse)  # ← Changed from "/chat" to "/"
async def chat_endpoint(request: ChatRequest):
    user_id = request.user_id
    session_id = request.session_id if request.session_id else f"default_session_{user_id}"
    user_message_content = request.message

    # 1. Save the user message
    user_message = Message(
        user_id=user_id,
        session_id=session_id,
        role="user",
        content=user_message_content,
        created_at=datetime.utcnow()
    )
    await mongo_manager.save_message(user_message)

    # 2. Short-term memory: fetch the last N messages for the session
    # Include the current user message in the window, so we fetch N-1 older messages
    short_term_messages = await mongo_manager.get_last_n_messages(
        user_id, session_id, settings.SHORT_TERM_N - 1
    )

    # Add the current user message to the short-term window for prompt composition
    short_term_messages.insert(0, user_message)  # Most recent at the beginning, will be reversed for prompt

    # 3. Long-term memory: fetch summaries
    latest_session_summary = await mongo_manager.get_latest_summary(user_id, "session", session_id)
    latest_lifetime_summary = await mongo_manager.get_latest_summary(user_id, "user", None)

    # 4. Episodic memory: extract facts from current message and retrieve relevant ones
    await extract_and_store_episodes(user_id, session_id, user_message_content)
    current_message_embedding = await generate_embedding(user_message_content)
    top_k_episodes = await mongo_manager.get_top_k_episodes_by_similarity(
        user_id, current_message_embedding, settings.EPISODE_RETRIEVAL_K
    )
    episodic_facts_retrieved = [ep.fact for ep in top_k_episodes]

    # 5. Compose the prompt
    ollama_messages_prompt = await compose_chat_prompt(
        user_id=user_id,
        session_id=session_id,
        current_message_content=user_message_content,
        short_term_messages=short_term_messages,
        latest_session_summary=latest_session_summary,
        latest_lifetime_summary=latest_lifetime_summary,
        episodic_facts=episodic_facts_retrieved
    )

    # 6. Call the Ollama chat API
    assistant_reply_content = await ollama_client.chat_completion(ollama_messages_prompt)

    # 7. Save the assistant message
    assistant_message = Message(
        user_id=user_id,
        session_id=session_id,
        role="assistant",
        content=assistant_reply_content,
        created_at=datetime.utcnow()
    )
    await mongo_manager.save_message(assistant_message)

    # 8. Long-term summarization trigger
    user_msg_count = await mongo_manager.count_user_messages_in_session(user_id, session_id)
    if user_msg_count % settings.SUMMARIZE_EVERY_USER_MSGS == 0:
        recent_session_messages = await mongo_manager.get_last_n_messages(
            user_id, session_id, settings.SHORT_TERM_N * 2
        )  # Get more messages for summary
        new_session_summary = await summarize_conversation(user_id, session_id, recent_session_messages)
        if new_session_summary:
            await mongo_manager.upsert_summary(new_session_summary)

        # Recompute lifetime summary occasionally
        await refresh_lifetime_summary(user_id)

    # 9. Return structured response
    return ChatResponse(
        assistant_reply=assistant_reply_content,
        short_term_messages_count=len(short_term_messages),
        long_term_summary_text=latest_session_summary.text if latest_session_summary else None,
        episodic_facts_retrieved=episodic_facts_retrieved
    )