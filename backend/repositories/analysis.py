from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.repositories.base import BaseRepository
from backend.models.models import AnalysisHistory
from backend.database.collections import ANALYSIS_HISTORY_COLLECTION

class AnalysisRepository(BaseRepository[AnalysisHistory]):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, ANALYSIS_HISTORY_COLLECTION, AnalysisHistory)

    async def find_by_repository_id(self, repository_id: str) -> List[AnalysisHistory]:
        """
        Fetch the analysis log history for a repository
        """
        cursor = self.collection.find({"repository_id": repository_id})
        docs = await cursor.to_list(length=100)
        return [self.model_class(**doc) for doc in docs]

    async def find_by_review_id(self, review_id: str) -> Optional[AnalysisHistory]:
        """
        Fetch the analysis log for a specific review run
        """
        doc = await self.collection.find_one({"review_id": review_id})
        return self.model_class(**doc) if doc else None
