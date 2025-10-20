from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
import os

# Import your Mongo manager and routers
from ai_memory_fastapi.mongoimpl.mongo import mongo_manager
from ai_memory_fastapi.routers import chat, memory, aggregate


# ------------------------------
# FastAPI App with Lifespan Hook
# ------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles MongoDB connection setup and teardown."""
    await mongo_manager.connect_to_mongo()
    yield
    await mongo_manager.close_mongo_connection()


# ------------------------------
# Initialize App
# ------------------------------
app = FastAPI(lifespan=lifespan, title="AI Memory FastAPI")


# ------------------------------
# Include Routers
# ------------------------------
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])  # ← Updated prefix
app.include_router(aggregate.router, prefix="/api/aggregate", tags=["Aggregate"])
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")


# ------------------------------
# Root Endpoint
# ------------------------------
@app.get("/")
async def root():
    return {
        "message": "Welcome to AI Memory FastAPI! 🚀",
        "routes": [
            "/api/chat",
            "/api/memory/{user_id}",
            "/api/aggregate/{user_id}"
        ]
    }