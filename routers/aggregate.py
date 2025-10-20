from fastapi import APIRouter
from ..mongoimpl.mongo import mongo_manager
from pymongo import ASCENDING

router = APIRouter()  # ← Removed prefix="/api/aggregate"

@router.get("/{user_id}")
async def aggregate_user_data(user_id: str):
    """
    Returns daily message counts and recent summaries for a user.
    """
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": ASCENDING}}
    ]
    results = await mongo_manager.db.messages.aggregate(pipeline).to_list(length=100)
    recent_summaries = await mongo_manager.get_all_session_summaries(user_id)

    return {
        "daily_message_counts": results,
        "recent_summaries": [s.text for s in recent_summaries[:3]]
    }