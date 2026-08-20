"""Async MongoDB connection via Motor.

Provides:
- client: Motor async client
- db: default database handle
- get_mongo_db: FastAPI dependency
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongo_uri)
db: AsyncIOMotorDatabase = client.get_default_database()

# Named collection accessors
solution_reviews = db.solution_reviews


async def get_mongo_db() -> AsyncIOMotorDatabase:
    """FastAPI dependency — returns the MongoDB database handle."""
    return db
