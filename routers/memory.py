from fastapi import APIRouter
from ..mongoimpl.mongo import mongo_manager

router = APIRouter()  # ← Removed prefix="/api/memory"

@router.get("/{user_id}")
async def get_memory_snapshot(user_id: str):
    """
    Returns a consolidated memory snapshot:
    - Last 16 messages
    - Latest session summary
    - Latest lifetime summary
    - Last 20 episodic facts
    """
    messages = await mongo_manager.get_last_n_messages(user_id, None, 16)
    session_summary = await mongo_manager.get_latest_summary(user_id, "session")
    lifetime_summary = await mongo_manager.get_latest_summary(user_id, "user")
    episodic_facts = await mongo_manager.get_last_n_episodic_facts(user_id, 20)

    return {
        "messages": [m.model_dump() for m in messages],
        "latest_session_summary": session_summary.text if session_summary else None,
        "latest_lifetime_summary": lifetime_summary.text if lifetime_summary else None,
        "episodic_facts": episodic_facts
    }