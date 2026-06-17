import logging
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ConfigurationError
from backend.config.settings import settings

logger = logging.getLogger("RepoMindAI.database")

class MockCursor:
    def __init__(self, data):
        self.data = data
        self._index = 0

    def sort(self, *args, **kwargs):
        if args and args[0]:
            sort_key, direction = args[0][0]
            self.data = sorted(
                self.data,
                key=lambda x: x.get(sort_key) if x.get(sort_key) is not None else datetime.min,
                reverse=(direction == -1)
            )
        return self

    def skip(self, n):
        self.data = self.data[n:]
        return self

    def limit(self, n):
        self.data = self.data[:n]
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self.data):
            raise StopAsyncIteration
        val = self.data[self._index]
        self._index += 1
        return val

    async def to_list(self, length=None):
        if length is not None:
            return self.data[:length]
        return self.data

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.documents = []

    async def create_index(self, keys, unique=False):
        pass

    async def find_one(self, query):
        for doc in self.documents:
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return dict(doc)
        return None

    async def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        self.documents.append(doc)
        class InsertResult:
            inserted_id = doc["_id"]
        return InsertResult()

    async def find_one_and_update(self, query, update, return_document=True):
        doc = None
        for d in self.documents:
            match = True
            for k, v in query.items():
                if d.get(k) != v:
                    match = False
                    break
            if match:
                doc = d
                break
        if doc and "$set" in update:
            for k, v in update["$set"].items():
                doc[k] = v
        return dict(doc) if doc else None

    async def update_one(self, query, update):
        doc = None
        for d in self.documents:
            match = True
            for k, v in query.items():
                if d.get(k) != v:
                    match = False
                    break
            if match:
                doc = d
                break
        if doc and "$set" in update:
            for k, v in update["$set"].items():
                doc[k] = v
        class UpdateResult:
            modified_count = 1 if doc else 0
        return UpdateResult()

    async def delete_one(self, query):
        doc = None
        for d in self.documents:
            match = True
            for k, v in query.items():
                if d.get(k) != v:
                    match = False
                    break
            if match:
                doc = d
                break
        if doc:
            self.documents.remove(doc)
        class DeleteResult:
            deleted_count = 1 if doc else 0
        return DeleteResult()

    def find(self, query=None):
        query = query or {}
        matched = []
        for doc in self.documents:
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                matched.append(dict(doc))
        return MockCursor(matched)

    async def count_documents(self, query):
        count = 0
        for doc in self.documents:
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                count += 1
        return count

class MockDatabase:
    def __init__(self):
        self.collections = {}

    @property
    def name(self):
        return "repomind_mock"

    async def command(self, cmd_name, *args, **kwargs):
        if cmd_name == "ping":
            return {"ok": 1.0}
        return {}

    async def list_collection_names(self):
        return list(self.collections.keys())

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

db_instance = MongoDB()

async def connect_to_mongodb():
    """
    Establish an asynchronous connection pool to MongoDB Atlas
    """
    if db_instance.client is not None:
        logger.warning("MongoDB client is already connected.")
        return
        
    logger.info("Initializing MongoDB Atlas Connection...")
    try:
        db_instance.client = AsyncIOMotorClient(
            settings.mongodb_uri,
            maxPoolSize=100,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
            retryWrites=True
        )
        await db_instance.client.admin.command('ping')
        db_instance.db = db_instance.client[settings.database_name]
        logger.info(f"MongoDB Connected Successfully. Database: {settings.database_name}")
    except Exception as e:
        logger.error(f"MongoDB Connection Failure: {e}")
        logger.warning("----------------------------------------------------------------------")
        logger.warning("FALLING BACK TO IN-MEMORY MOCK DATABASE FOR LOCAL TESTING/DEVELOPMENT!")
        logger.warning("----------------------------------------------------------------------")
        db_instance.client = None
        db_instance.db = MockDatabase()

async def close_mongodb_connection():
    """
    Shut down the connection pool cleanly
    """
    if db_instance.client is None:
        logger.warning("MongoDB client is not connected.")
        return
    logger.info("Closing MongoDB connections...")
    db_instance.client.close()
    db_instance.client = None
    db_instance.db = None
    logger.info("MongoDB connection closed successfully.")

def get_database():
    """
    Retrieve the database instance (Singleton provider)
    """
    if db_instance.db is None:
        raise RuntimeError("Database connection has not been initialized. Call connect_to_mongodb() first.")
    return db_instance.db
