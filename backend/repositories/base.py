from typing import TypeVar, Generic, List, Optional, Dict, Any
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

T = TypeVar('T', bound=BaseModel)

class BaseRepository(Generic[T]):
    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str, model_class: type[T]):
        self.db = db
        self.collection = db[collection_name]
        self.model_class = model_class

    async def create(self, model_data: BaseModel) -> T:
        """
        Insert a new document into MongoDB
        """
        data = model_data.model_dump(by_alias=True, exclude_unset=True)
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        
        result = await self.collection.insert_one(data)
        created_doc = await self.collection.find_one({"_id": result.inserted_id})
        return self.model_class(**created_doc)

    async def find_by_id(self, doc_id: str) -> Optional[T]:
        """
        Find a single document by its ObjectId string
        """
        if not doc_id or not ObjectId.is_valid(doc_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(doc_id)})
        return self.model_class(**doc) if doc else None

    async def find_all(self, query: Dict[str, Any] = None, skip: int = 0, limit: int = 100, sort: List[tuple] = None) -> List[T]:
        """
        Find all matching documents with support for pagination and sorting
        """
        query = query or {}
        cursor = self.collection.find(query)
        if sort:
            cursor = cursor.sort(sort)
        cursor = cursor.skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self.model_class(**doc) for doc in docs]

    async def update(self, doc_id: str, update_data: Dict[str, Any]) -> Optional[T]:
        """
        Update a document by its ObjectId string
        """
        if not doc_id or not ObjectId.is_valid(doc_id):
            return None
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(doc_id)},
            {"$set": update_data},
            return_document=True
        )
        return self.model_class(**result) if result else None

    async def delete(self, doc_id: str) -> bool:
        """
        Delete a document by its ObjectId string
        """
        if not doc_id or not ObjectId.is_valid(doc_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(doc_id)})
        return result.deleted_count > 0
