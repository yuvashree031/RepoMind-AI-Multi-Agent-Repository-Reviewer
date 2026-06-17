from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.repositories.base import BaseRepository
from backend.models.models import Review
from backend.database.collections import REVIEWS_COLLECTION

class ReviewRepository(BaseRepository[Review]):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, REVIEWS_COLLECTION, Review)

    async def find_by_repository_id(self, repository_id: str) -> List[Review]:
        """
        Fetch all audit reviews belonging to a given repository
        """
        cursor = self.collection.find({"repository_id": repository_id})
        docs = await cursor.to_list(length=100)
        return [self.model_class(**doc) for doc in docs]
