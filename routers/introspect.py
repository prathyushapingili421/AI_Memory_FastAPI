from fastapi import APIRouter
from typing import List, Optional # Ensure Optional and List are imported
from datetime import datetime, timedelta
from collections import defaultdict

from ..models import MemoryViewResponse, AggregateResponse, DailyMessageCount, Message, Summary
from ..mongoimpl.mongo import mongo_manager

router = APIRouter()

@router.get("/memory/{user_id}", response_model=MemoryViewResponse)
async def get_memory_view(user_id: str, session_id: Optional[str] = None):
    # Default session if not provided
    session_id_to_use = session_id if session_id else f"default_session_{user_id}"

    # Last ~16 messages
    last_messages = await mongo_manager.get_last_n_messages(user_id, session_id_to_use, 16)

    # Latest session summary
    latest_session_summary = await mongo_manager.get_latest_summary(user_id, "session", session_id_to_use)

    # Latest lifetime user summary
    latest_lifetime_summary = await mongo_manager.get_latest_summary(user_id, "user", None)

    # Last ~20 episodic facts (text only)
    last_episodic_facts = await mongo_manager.get_last_n_episodic_facts(user_id, 20)

    return MemoryViewResponse(
        last_messages=last_messages,
        latest_session_summary=latest_session_summary,
        latest_lifetime_summary=latest_lifetime_summary,
        last_episodic_facts=last_episodic_facts
    )

@router.get("/aggregate/{user_id}", response_model=AggregateResponse)
async def get_aggregate_data(user_id: str):
    # Daily message counts
    all_user_messages = await mongo_manager.get_last_n_messages(user_id, None, 1000) # Fetch up to 1000 messages for aggregation
    
    daily_counts = defaultdict(int)
    for msg in all_user_messages:
        date_str = msg.created_at.strftime("%Y-%m-%d")
        daily_counts[date_str] += 1
    
    daily_message_counts = [
        DailyMessageCount(date=date, count=count) 
        for date, count in sorted(daily_counts.items())
    ]

    # Recent summaries (lifetime + latest session)
    recent_summaries: List[Summary] = []
    latest_lifetime_summary = await mongo_manager.get_latest_summary(user_id, "user", None)
    if latest_lifetime_summary:
        recent_summaries.append(latest_lifetime_summary)
    
    default_session_id = f"default_session_{user_id}"
    latest_session_summary = await mongo_manager.get_latest_summary(user_id, "session", default_session_id)
    if latest_session_summary:
         recent_summaries.append(latest_session_summary)
    
    return AggregateResponse(
        daily_message_counts=daily_message_counts,
        recent_summaries=recent_summaries
    )