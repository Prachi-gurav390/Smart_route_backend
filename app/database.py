from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ServerSelectionTimeoutError
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class Database:
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None


database = Database()


async def connect_to_mongo():
    """Create database connection with timeout"""
    try:
        # Add connection timeout to prevent hanging
        database.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        database.database = database.client[settings.DATABASE_NAME]

        # Test connection with timeout
        await database.client.admin.command('ping')
        logger.info("Connected to MongoDB successfully")

        # Create indexes
        await create_indexes()

    except ServerSelectionTimeoutError as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise


async def close_mongo_connection():
    """Close database connection"""
    if database.client:
        database.client.close()
        logger.info("Disconnected from MongoDB")


async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance, connecting if necessary"""
    if database.database is None:
        await connect_to_mongo()
    return database.database


async def create_indexes():
    """Create necessary database indexes"""
    db = database.database

    # Geospatial index for stops
    await db.stops.create_index([("location", "2dsphere")])

    # Index for efficient lookups
    await db.stops.create_index("stop_id", unique=True)
    await db.routes.create_index("route_id", unique=True)
    await db.stops.create_index("name")

    logger.info("Database indexes created")
