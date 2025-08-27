"""
Load sample transport data for testing
"""
from app.config import settings
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Sample data for a small city transport network
SAMPLE_STOPS = [
    {"stop_id": "S001", "name": "Central Station", "lat": 12.9716, "lon": 77.5946},
    {"stop_id": "S002", "name": "MG Road", "lat": 12.9759, "lon": 77.6081},
    {"stop_id": "S003", "name": "Brigade Road", "lat": 12.9718, "lon": 77.6108},
    {"stop_id": "S004", "name": "Commercial Street", "lat": 12.9833, "lon": 77.6097},
    {"stop_id": "S005", "name": "Shivaji Nagar", "lat": 13.0067, "lon": 77.6033},
    {"stop_id": "S006", "name": "Cubbon Park", "lat": 12.9698, "lon": 77.5931},
    {"stop_id": "S007", "name": "Vidhana Soudha", "lat": 12.9796, "lon": 77.5911},
    {"stop_id": "S008", "name": "Majestic", "lat": 12.9769, "lon": 77.5703},
    {"stop_id": "S009", "name": "City Railway Station",
        "lat": 12.9771, "lon": 77.5712},
    {"stop_id": "S010", "name": "KR Market", "lat": 12.9592, "lon": 77.5742},
]

SAMPLE_ROUTES = [
    {
        "route_id": "R001",
        "name": "City Circle",
        "stops": ["S001", "S002", "S003", "S004", "S005"],
        "route_type": "bus"
    },
    {
        "route_id": "R002",
        "name": "Metro Red Line",
        "stops": ["S001", "S006", "S007", "S008"],
        "route_type": "metro"
    },
    {
        "route_id": "R003",
        "name": "Express Line",
        "stops": ["S008", "S009", "S010", "S001"],
        "route_type": "bus"
    },
]


async def create_connections():
    """Create connections between stops based on routes"""
    connections = {}

    for route in SAMPLE_ROUTES:
        route_id = route["route_id"]
        stops = route["stops"]
        route_type = route["route_type"]

        # Base time and cost based on route type
        if route_type == "metro":
            base_time = 3
            base_cost = 2.0
        else:  # bus
            base_time = 5
            base_cost = 1.5

        for i in range(len(stops) - 1):
            from_stop = stops[i]
            to_stop = stops[i + 1]

            if from_stop not in connections:
                connections[from_stop] = []

            # Add some variation to time and cost
            time_variation = i % 3  # 0, 1, or 2 extra minutes
            cost_variation = (i % 3) * 0.5  # 0, 0.5, or 1.0 extra cost

            connections[from_stop].append({
                "to_stop_id": to_stop,
                "route_id": route_id,
                "time": base_time + time_variation,
                "cost": base_cost + cost_variation,
                "sequence": i + 1
            })

            # Add reverse direction with slightly different time/cost
            if to_stop not in connections:
                connections[to_stop] = []

            connections[to_stop].append({
                "to_stop_id": from_stop,
                "route_id": route_id,
                "time": base_time + time_variation + 1,
                "cost": base_cost + cost_variation,
                "sequence": len(stops) - i
            })

    return connections


async def load_sample_data():
    """Load sample data into MongoDB"""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    try:
        # Clear existing data
        await db.stops.delete_many({})
        await db.routes.delete_many({})
        print("Cleared existing data")

        # Create connections
        connections = await create_connections()

        # Insert stops with connections
        stops_to_insert = []
        for stop in SAMPLE_STOPS:
            stop_doc = {
                "stop_id": stop["stop_id"],
                "name": stop["name"],
                "location": {
                    "type": "Point",
                    "coordinates": [stop["lon"], stop["lat"]]
                },
                "connections": connections.get(stop["stop_id"], [])
            }
            stops_to_insert.append(stop_doc)

        await db.stops.insert_many(stops_to_insert)
        print(f"Inserted {len(stops_to_insert)} stops")

        # Insert routes
        await db.routes.insert_many(SAMPLE_ROUTES)
        print(f"Inserted {len(SAMPLE_ROUTES)} routes")

        # Create indexes
        await db.stops.create_index([("location", "2dsphere")])
        await db.stops.create_index("stop_id", unique=True)
        await db.routes.create_index("route_id", unique=True)
        print("Created indexes")
 
        print("Sample data loaded successfully!")

    except Exception as e:
        print(f"Error loading sample data: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(load_sample_data())
