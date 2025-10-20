from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class Message(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    role: str # "user" or "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Summary(BaseModel):
    user_id: str
    session_id: Optional[str] = None # Nullable for lifetime summary
    scope: str # "session" or "user"
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Episode(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    fact: str
    importance: float # 0.0 to 1.0
    embedding: List[float]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    assistant_reply: str
    short_term_messages_count: int
    long_term_summary_text: Optional[str] = None
    episodic_facts_retrieved: List[str]

class MemoryViewResponse(BaseModel):
    last_messages: List[Message]
    latest_session_summary: Optional[Summary] = None
    latest_lifetime_summary: Optional[Summary] = None
    last_episodic_facts: List[str]

class DailyMessageCount(BaseModel):
    date: str
    count: int

class AggregateResponse(BaseModel):
    daily_message_counts: List[DailyMessageCount]
    recent_summaries: List[Summary]