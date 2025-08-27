#!/usr/bin/env python3
"""
Load data to MongoDB Atlas for production deployment
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import sys
import logging

# Add app to path
sys.path.append('.')
from scripts.load_comprehensive_data import load_comprehensive_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def load_data_to_atlas():
    """Load data directly to MongoDB Atlas"""
    
    # Get MongoDB URL from environment or prompt user
    mongodb_url = os.getenv('MONGODB_URL')
    if not mongodb_url:
        print("MongoDB Atlas connection string not found in environment.")
        mongodb_url = input("Enter your MongoDB Atlas connection string: ")
    
    database_name = os.getenv('DATABASE_NAME', 'smartroute')
    
    print(f"Connecting to MongoDB Atlas...")
    print(f"Database: {database_name}")
    
    try:
        # Connect to MongoDB Atlas
        client = AsyncIOMotorClient(mongodb_url, serverSelectionTimeoutMS=30000)
        db = client[database_name]
        
        # Test connection
        await client.admin.command('ping')
        logger.info("✓ Connected to MongoDB Atlas successfully")
        
        # Check if data already exists
        stops_count = await db.stops.count_documents({})
        routes_count = await db.routes.count_documents({})
        
        if stops_count > 0 or routes_count > 0:
            print(f"Database already contains data: {stops_count} stops, {routes_count} routes")
            overwrite = input("Overwrite existing data? (y/N): ").lower().strip()
            if overwrite != 'y':
                print("Aborted.")
                return
                
            # Clear existing data
            await db.stops.delete_many({})
            await db.routes.delete_many({})
            logger.info("Cleared existing data")
        
        # Load comprehensive data
        logger.info("Loading comprehensive transport data...")
        await load_comprehensive_data(db)
        
        # Verify data was loaded
        final_stops = await db.stops.count_documents({})
        final_routes = await db.routes.count_documents({})
        
        logger.info(f"✓ Data loaded successfully!")
        logger.info(f"✓ Stops: {final_stops}")
        logger.info(f"✓ Routes: {final_routes}")
        
        # Create indexes
        logger.info("Creating database indexes...")
        await db.stops.create_index([("location", "2dsphere")])
        await db.stops.create_index("stop_id", unique=True)
        await db.routes.create_index("route_id", unique=True)
        await db.stops.create_index("name")
        logger.info("✓ Indexes created")
        
        print(f"""
🎉 SUCCESS! Your MongoDB Atlas database is ready.

Database: {database_name}
Stops: {final_stops}
Routes: {final_routes}

Your Render deployment can now connect to this database using:
MONGODB_URL={mongodb_url}
DATABASE_NAME={database_name}
""")
        
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    # Example usage:
    # export MONGODB_URL="mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority"
    # python load_data_to_atlas.py
    
    asyncio.run(load_data_to_atlas())