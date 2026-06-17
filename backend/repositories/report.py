from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.repositories.base import BaseRepository
from backend.models.models import Report
from backend.database.collections import REPORTS_COLLECTION

class ReportRepository(BaseRepository[Report]):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, REPORTS_COLLECTION, Report)

    async def find_by_review_id(self, review_id: str) -> Optional[Report]:
        """
        Fetch the generated report for a given review session ID
        """
        doc = await self.collection.find_one({"review_id": review_id})
        return self.model_class(**doc) if doc else None
