from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.repositories.base import BaseRepository
from backend.models.models import User
from backend.database.collections import USERS_COLLECTION

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, USERS_COLLECTION, User)

    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Find a user in the database by email address
        """
        doc = await self.collection.find_one({"email": email.strip().lower()})
        return self.model_class(**doc) if doc else None
