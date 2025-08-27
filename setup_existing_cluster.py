#!/usr/bin/env python3
"""
Setup SmartRoute database in existing MongoDB Atlas cluster
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

async def setup_existing_cluster():
    """Setup SmartRoute in existing MongoDB Atlas cluster"""
    
    print("🎯 SmartRoute Database Setup for Existing Cluster")
    print("=" * 60)
    
    # Get connection details
    mongodb_url = input("Enter your existing MongoDB Atlas connection string: ").strip()
    
    print("\nChoose setup option:")
    print("1. Create new database 'smartroute' (Recommended)")
    print("2. Use existing database with prefixed collections")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        database_name = "smartroute"
        collection_prefix = ""
    elif choice == "2":
        database_name = input("Enter existing database name: ").strip()
        collection_prefix = "smartroute_"
    else:
        print("Invalid choice!")
        return
    
    print(f"\nConfiguration:")
    print(f"MongoDB URL: {mongodb_url[:50]}...")
    print(f"Database: {database_name}")
    print(f"Collections: {collection_prefix}stops, {collection_prefix}routes")
    
    confirm = input("\nProceed with setup? (y/N): ").lower().strip()
    if confirm != 'y':
        print("Setup cancelled.")
        return
    
    try:
        # Connect to MongoDB Atlas
        client = AsyncIOMotorClient(mongodb_url, serverSelectionTimeoutMS=30000)
        db = client[database_name]
        
        # Test connection
        await client.admin.command('ping')
        logger.info("✓ Connected to MongoDB Atlas successfully")
        
        # Define collection names
        stops_collection = f"{collection_prefix}stops"
        routes_collection = f"{collection_prefix}routes"
        
        # Check if data already exists
        stops_count = await db[stops_collection].count_documents({})
        routes_count = await db[routes_collection].count_documents({})
        
        if stops_count > 0 or routes_count > 0:
            print(f"\nExisting data found: {stops_count} stops, {routes_count} routes")
            overwrite = input("Overwrite existing data? (y/N): ").lower().strip()
            if overwrite != 'y':
                print("Setup cancelled.")
                return
                
            # Clear existing data
            await db[stops_collection].delete_many({})
            await db[routes_collection].delete_many({})
            logger.info("Cleared existing data")
        
        # Load comprehensive data
        logger.info("Loading SmartRoute data...")
        
        # Temporarily modify collection names for loading if using prefix
        if collection_prefix:
            # We'll load to the prefixed collections
            original_db_stops = db.stops
            original_db_routes = db.routes
            db.stops = db[stops_collection]
            db.routes = db[routes_collection]
        
        await load_comprehensive_data(db)
        
        # Restore original references
        if collection_prefix:
            db.stops = original_db_stops
            db.routes = original_db_routes
        
        # Verify data was loaded
        final_stops = await db[stops_collection].count_documents({})
        final_routes = await db[routes_collection].count_documents({})
        
        logger.info(f"✓ Data loaded successfully!")
        logger.info(f"✓ Stops: {final_stops}")
        logger.info(f"✓ Routes: {final_routes}")
        
        # Create indexes
        logger.info("Creating database indexes...")
        await db[stops_collection].create_index([("location", "2dsphere")])
        await db[stops_collection].create_index("stop_id", unique=True)
        await db[routes_collection].create_index("route_id", unique=True)
        await db[stops_collection].create_index("name")
        logger.info("✓ Indexes created")
        
        # Show environment variables for deployment
        print(f"""
🎉 SUCCESS! SmartRoute database setup completed.

For Render deployment, use these environment variables:
┌─────────────────────────────────────────────────────────┐
│ MONGODB_URL={mongodb_url}
│ DATABASE_NAME={database_name}
└─────────────────────────────────────────────────────────┘

Database Details:
• Database: {database_name}
• Collections: {stops_collection}, {routes_collection}  
• Stops: {final_stops}
• Routes: {final_routes}
• Indexes: Created

Next Steps:
1. Copy the environment variables above
2. Add them to your Render web service
3. Deploy your application
4. Test using: python test_deployment.py <YOUR_RENDER_URL>
""")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(setup_existing_cluster())