import logging
from pymongo import ASCENDING, IndexModel
from backend.database.mongodb import get_database
from backend.database.collections import (
    USERS_COLLECTION,
    REPOSITORIES_COLLECTION,
    REVIEWS_COLLECTION,
    ANALYSIS_HISTORY_COLLECTION
)

logger = logging.getLogger("RepoMindAI.indexes")

async def create_indexes():
    """
    Automated generation of database indexes and unique constraints on startup
    """
    db = get_database()
    logger.info("Initializing database index validation...")
    try:
        await db[USERS_COLLECTION].create_index([("email", ASCENDING)], unique=True)
        logger.info(f"Verified unique index on {USERS_COLLECTION}(email)")

        await db[REPOSITORIES_COLLECTION].create_index([("url", ASCENDING)], unique=True)
        logger.info(f"Verified unique index on {REPOSITORIES_COLLECTION}(url)")

        await db[REVIEWS_COLLECTION].create_index([("repository_id", ASCENDING)])
        logger.info(f"Verified index on {REVIEWS_COLLECTION}(repository_id)")

        await db[ANALYSIS_HISTORY_COLLECTION].create_index([("repository_id", ASCENDING)])
        logger.info(f"Verified index on {ANALYSIS_HISTORY_COLLECTION}(repository_id)")
        
        logger.info("Database index creation completed.")
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}", exc_info=True)
        raise RuntimeError(f"Index creation failed: {e}") from e
