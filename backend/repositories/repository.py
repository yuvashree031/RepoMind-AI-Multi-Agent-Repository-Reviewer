from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.repositories.base import BaseRepository
from backend.models.models import Repository
from backend.database.collections import REPOSITORIES_COLLECTION

class RepositoryRepository(BaseRepository[Repository]):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, REPOSITORIES_COLLECTION, Repository)

    async def find_by_url(self, url: str) -> Optional[Repository]:
        """
        Find a repository configuration by its source URL
        """
        doc = await self.collection.find_one({"url": url.strip()})
        return self.model_class(**doc) if doc else None
