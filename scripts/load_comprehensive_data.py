"""
Load comprehensive transport data for realistic testing
This creates a realistic multi-modal transit network similar to major cities
"""
import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from geopy.distance import geodesic
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings


# Comprehensive transit network inspired by Bangalore
COMPREHENSIVE_STOPS = [
    # Metro Red Line (North-South)
    {"stop_id": "M001", "name": "Baiyappanahalli", "lat": 12.9908, "lon": 77.6503, "zone": "east"},
    {"stop_id": "M002", "name": "Swami Vivekananda Road", "lat": 12.9793, "lon": 77.6367, "zone": "central"},
    {"stop_id": "M003", "name": "Indiranagar", "lat": 12.9784, "lon": 77.6408, "zone": "central"},
    {"stop_id": "M004", "name": "Halasuru", "lat": 12.9756, "lon": 77.6276, "zone": "central"},
    {"stop_id": "M005", "name": "Trinity", "lat": 12.9735, "lon": 77.6203, "zone": "central"},
    {"stop_id": "M006", "name": "MG Road", "lat": 12.9759, "lon": 77.6081, "zone": "central"},
    {"stop_id": "M007", "name": "Cubbon Park", "lat": 12.9698, "lon": 77.5931, "zone": "central"},
    {"stop_id": "M008", "name": "Vidhana Soudha", "lat": 12.9796, "lon": 77.5911, "zone": "central"},
    {"stop_id": "M009", "name": "Sir M Visvesvaraya Station Central College", "lat": 12.9764, "lon": 77.5844, "zone": "central"},
    {"stop_id": "M010", "name": "Majestic", "lat": 12.9769, "lon": 77.5703, "zone": "central"},
    {"stop_id": "M011", "name": "City Railway Station", "lat": 12.9771, "lon": 77.5712, "zone": "central"},
    {"stop_id": "M012", "name": "Magadi Road", "lat": 12.9689, "lon": 77.5633, "zone": "west"},
    {"stop_id": "M013", "name": "Hosahalli", "lat": 12.9622, "lon": 77.5547, "zone": "west"},
    {"stop_id": "M014", "name": "Vijayanagar", "lat": 12.9546, "lon": 77.5392, "zone": "west"},
    {"stop_id": "M015", "name": "Attiguppe", "lat": 12.9456, "lon": 77.5239, "zone": "west"},
    {"stop_id": "M016", "name": "Deepanjali Nagar", "lat": 12.9367, "lon": 77.5086, "zone": "west"},
    {"stop_id": "M017", "name": "Mysuru Road", "lat": 12.9278, "lon": 77.4933, "zone": "west"},

    # Metro Purple Line (East-West)
    {"stop_id": "P001", "name": "Whitefield", "lat": 12.9698, "lon": 77.7500, "zone": "east"},
    {"stop_id": "P002", "name": "Kadugodi", "lat": 12.9789, "lon": 77.7356, "zone": "east"},
    {"stop_id": "P003", "name": "Hoodi", "lat": 12.9867, "lon": 77.7156, "zone": "east"},
    {"stop_id": "P004", "name": "Garudacharpalya", "lat": 12.9845, "lon": 77.6989, "zone": "east"},
    {"stop_id": "P005", "name": "Mahadevapura", "lat": 12.9823, "lon": 77.6822, "zone": "east"},
    {"stop_id": "P006", "name": "Baiyyappanahalli", "lat": 12.9908, "lon": 77.6503, "zone": "east"},  # Interchange
    {"stop_id": "P007", "name": "Benniganahalli", "lat": 12.9789, "lon": 77.6322, "zone": "central"},
    {"stop_id": "P008", "name": "K R Puram", "lat": 13.0056, "lon": 77.6203, "zone": "central"},
    {"stop_id": "P009", "name": "Byappanahalli", "lat": 13.0122, "lon": 77.6089, "zone": "central"},
    {"stop_id": "P010", "name": "Nagasandra", "lat": 13.0289, "lon": 77.5033, "zone": "north"},

    # Bus Routes - Major Corridors
    # Electronic City - CBD
    {"stop_id": "B001", "name": "Electronic City Phase 1", "lat": 12.8456, "lon": 77.6603, "zone": "south"},
    {"stop_id": "B002", "name": "Electronic City Phase 2", "lat": 12.8389, "lon": 77.6756, "zone": "south"},
    {"stop_id": "B003", "name": "Bommasandra", "lat": 12.8067, "lon": 77.6367, "zone": "south"},
    {"stop_id": "B004", "name": "Anekal", "lat": 12.7103, "lon": 77.6956, "zone": "south"},
    {"stop_id": "B005", "name": "Chandapura", "lat": 12.7756, "lon": 77.6856, "zone": "south"},
    {"stop_id": "B006", "name": "Hosur Road Silk Board", "lat": 12.9176, "lon": 77.6233, "zone": "south"},
    {"stop_id": "B007", "name": "BTM Layout", "lat": 12.9165, "lon": 77.6101, "zone": "south"},
    {"stop_id": "B008", "name": "Jayanagar 4th Block", "lat": 12.9237, "lon": 77.5899, "zone": "south"},
    {"stop_id": "B009", "name": "Lalbagh West Gate", "lat": 12.9507, "lon": 77.5836, "zone": "central"},
    {"stop_id": "B010", "name": "KR Market", "lat": 12.9592, "lon": 77.5742, "zone": "central"},

    # Outer Ring Road Corridor
    {"stop_id": "B011", "name": "Marathahalli", "lat": 12.9591, "lon": 77.6974, "zone": "east"},
    {"stop_id": "B012", "name": "Kadubeesanahalli", "lat": 12.9341, "lon": 77.6789, "zone": "east"},
    {"stop_id": "B013", "name": "Bellandur", "lat": 12.9248, "lon": 77.6733, "zone": "east"},
    {"stop_id": "B014", "name": "Ecospace", "lat": 12.9122, "lon": 77.6556, "zone": "east"},
    {"stop_id": "B015", "name": "Agara", "lat": 12.9067, "lon": 77.6344, "zone": "east"},
    {"stop_id": "B016", "name": "HSR Layout", "lat": 12.9082, "lon": 77.6456, "zone": "south"},
    {"stop_id": "B017", "name": "Koramangala", "lat": 12.9352, "lon": 77.6245, "zone": "central"},
    {"stop_id": "B018", "name": "Sony World Signal", "lat": 12.9289, "lon": 77.6156, "zone": "central"},

    # North Bangalore
    {"stop_id": "B019", "name": "Hebbal", "lat": 13.0358, "lon": 77.5972, "zone": "north"},
    {"stop_id": "B020", "name": "RT Nagar", "lat": 13.0189, "lon": 77.5956, "zone": "north"},
    {"stop_id": "B021", "name": "Sahakar Nagar", "lat": 13.0456, "lon": 77.5789, "zone": "north"},
    {"stop_id": "B022", "name": "Manyata Tech Park", "lat": 13.0456, "lon": 77.6203, "zone": "north"},
    {"stop_id": "B023", "name": "Yelahanka", "lat": 13.1007, "lon": 77.5963, "zone": "north"},

    # West Bangalore
    {"stop_id": "B024", "name": "Rajajinagar", "lat": 12.9914, "lon": 77.5544, "zone": "west"},
    {"stop_id": "B025", "name": "Malleswaram", "lat": 13.0033, "lon": 77.5703, "zone": "west"},
    {"stop_id": "B026", "name": "Yeshwantpur", "lat": 13.0281, "lon": 77.5544, "zone": "west"},
    {"stop_id": "B027", "name": "Peenya", "lat": 13.0281, "lon": 77.5203, "zone": "west"},
    {"stop_id": "B028", "name": "Jalahalli", "lat": 13.0456, "lon": 77.5403, "zone": "west"},

    # Additional important locations
    {"stop_id": "B029", "name": "Brigade Road", "lat": 12.9718, "lon": 77.6108, "zone": "central"},
    {"stop_id": "B030", "name": "Commercial Street", "lat": 12.9833, "lon": 77.6097, "zone": "central"},
    {"stop_id": "B031", "name": "Shivaji Nagar", "lat": 13.0067, "lon": 77.6033, "zone": "central"},
    {"stop_id": "B032", "name": "Cunningham Road", "lat": 12.9889, "lon": 77.5911, "zone": "central"},
    {"stop_id": "B033", "name": "Richmond Road", "lat": 12.9611, "lon": 77.6089, "zone": "central"},
    {"stop_id": "B034", "name": "Domlur", "lat": 12.9611, "lon": 77.6389, "zone": "central"},
    {"stop_id": "B035", "name": "Airport Road", "lat": 13.0192, "lon": 77.6408, "zone": "north"},

    # Tech Parks and Employment Hubs
    {"stop_id": "T001", "name": "ITPL Whitefield", "lat": 12.9845, "lon": 77.7467, "zone": "east"},
    {"stop_id": "T002", "name": "Bagmane Tech Park", "lat": 12.9678, "lon": 77.7456, "zone": "east"},
    {"stop_id": "T003", "name": "Prestige Tech Park", "lat": 12.9567, "lon": 77.6978, "zone": "east"},
    {"stop_id": "T004", "name": "Embassy Golf Links", "lat": 12.9678, "lon": 77.6456, "zone": "central"},
    {"stop_id": "T005", "name": "UB City Mall", "lat": 12.9689, "lon": 77.6156, "zone": "central"},
]

COMPREHENSIVE_ROUTES = [
    # Metro Red Line (North-South)
    {
        "route_id": "METRO_RED",
        "name": "Metro Red Line - Baiyappanahalli to Mysuru Road",
        "stops": ["M001", "M002", "M003", "M004", "M005", "M006", "M007", 
                 "M008", "M009", "M010", "M011", "M012", "M013", "M014", 
                 "M015", "M016", "M017"],
        "route_type": "metro"
    },
    
    # Metro Purple Line (East-West) 
    {
        "route_id": "METRO_PURPLE",
        "name": "Metro Purple Line - Whitefield to Nagasandra",
        "stops": ["P001", "P002", "P003", "P004", "P005", "P006", "P007", 
                 "P008", "P009", "P010"],
        "route_type": "metro"
    },

    # High Frequency Bus Routes
    {
        "route_id": "BUS_500E",
        "name": "500E - Electronic City Express",
        "stops": ["B001", "B002", "B006", "B007", "B008", "B009", "B010", 
                 "M010", "M007", "B029", "M006"],
        "route_type": "bus"
    },
    
    {
        "route_id": "BUS_201",
        "name": "201 - Outer Ring Road",
        "stops": ["B011", "B012", "B013", "B014", "B015", "B016", "B017", 
                 "B018", "M006", "M007"],
        "route_type": "bus"
    },
    
    {
        "route_id": "BUS_280",
        "name": "280 - North Bangalore Connector",
        "stops": ["B019", "B020", "B021", "B022", "M008", "M007", "M006"],
        "route_type": "bus"
    },
    
    {
        "route_id": "BUS_335",
        "name": "335 - West Bangalore Local",
        "stops": ["B024", "B025", "B026", "M008", "M007", "B032", "B031"],
        "route_type": "bus"
    },

    # Tech Park Shuttles
    {
        "route_id": "SHUTTLE_WF",
        "name": "Whitefield Tech Shuttle",
        "stops": ["T001", "T002", "P001", "P002", "B011", "M003"],
        "route_type": "bus"
    },
    
    {
        "route_id": "SHUTTLE_ORR",
        "name": "ORR Tech Parks Express",
        "stops": ["T003", "B011", "B012", "B013", "T004", "B017", "M006"],
        "route_type": "bus"
    },

    # Cross-City Routes
    {
        "route_id": "BUS_400",
        "name": "400 - City Circle",
        "stops": ["M006", "B029", "B030", "B031", "B032", "B025", "M008", 
                 "M007", "B010", "B008", "B017", "B034", "M003"],
        "route_type": "bus"
    },
    
    {
        "route_id": "BUS_G4",
        "name": "G4 - Airport Express",
        "stops": ["B035", "B022", "B019", "B031", "M008", "M006"],
        "route_type": "bus"
    },

    # Feeder Routes to Metro
    {
        "route_id": "BUS_F1",
        "name": "F1 - Koramangala Metro Feeder",
        "stops": ["B016", "B017", "B018", "M006"],
        "route_type": "bus"
    },
    
    {
        "route_id": "BUS_F2", 
        "name": "F2 - Jayanagar Metro Feeder",
        "stops": ["B008", "B009", "B010", "M010"],
        "route_type": "bus"
    },
]


def calculate_realistic_time_and_cost(from_stop, to_stop, route_info, sequence):
    """Calculate realistic travel time and cost based on distance and route type"""
    
    # Find stop coordinates
    from_coords = None
    to_coords = None
    
    for stop in COMPREHENSIVE_STOPS:
        if stop["stop_id"] == from_stop:
            from_coords = (stop["lat"], stop["lon"])
        elif stop["stop_id"] == to_stop:
            to_coords = (stop["lat"], stop["lon"])
    
    if not from_coords or not to_coords:
        # Default values if coordinates not found
        return 5, 2.0
    
    # Calculate distance
    distance_km = geodesic(from_coords, to_coords).kilometers
    
    route_type = route_info["route_type"]
    
    if route_type == "metro":
        # Metro: faster, more expensive
        # Average speed: 35 km/h + 1 minute station stop
        time = max(2, int((distance_km / 35) * 60) + 1)
        cost = max(10, distance_km * 15)  # ₹15 per km base
        
    else:  # bus
        # Bus: slower due to traffic, cheaper
        # Average speed varies by route type
        if "Express" in route_info["name"] or "Shuttle" in route_info["name"]:
            # Express routes: 25 km/h average
            time = max(3, int((distance_km / 25) * 60) + 1)
            cost = max(5, distance_km * 8)  # ₹8 per km
        else:
            # Local routes: 20 km/h average with more stops
            time = max(4, int((distance_km / 20) * 60) + 2)
            cost = max(5, distance_km * 6)  # ₹6 per km
    
    # Add some realistic variation
    time_variation = random.randint(-1, 2)
    cost_variation = random.uniform(-0.5, 1.0)
    
    return max(1, time + time_variation), max(1.0, cost + cost_variation)


async def create_comprehensive_connections():
    """Create realistic connections between stops based on routes"""
    connections = {}
    
    for route in COMPREHENSIVE_ROUTES:
        route_id = route["route_id"]
        stops = route["stops"]
        
        print(f"Processing route {route_id} with {len(stops)} stops...")
        
        # Forward direction
        for i in range(len(stops) - 1):
            from_stop = stops[i]
            to_stop = stops[i + 1]
            
            if from_stop not in connections:
                connections[from_stop] = []
            
            time, cost = calculate_realistic_time_and_cost(from_stop, to_stop, route, i + 1)
            
            connections[from_stop].append({
                "to_stop_id": to_stop,
                "route_id": route_id,
                "time": time,
                "cost": cost,
                "sequence": i + 1
            })
        
        # Reverse direction (slightly different timing due to traffic patterns)
        for i in range(len(stops) - 1, 0, -1):
            from_stop = stops[i]
            to_stop = stops[i - 1]
            
            if from_stop not in connections:
                connections[from_stop] = []
            
            time, cost = calculate_realistic_time_and_cost(from_stop, to_stop, route, len(stops) - i)
            # Add slight variation for reverse direction
            time += random.randint(0, 1)
            
            connections[from_stop].append({
                "to_stop_id": to_stop,
                "route_id": route_id,
                "time": time,
                "cost": cost,
                "sequence": len(stops) - i
            })
    
    print(f"Created connections for {len(connections)} stops")
    return connections


async def load_comprehensive_data(db=None):
    """Load comprehensive realistic data into MongoDB"""
    if db is None:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        should_close = True
    else:
        should_close = False
        client = None
    
    try:
        print("Clearing existing data...")
        await db.stops.delete_many({})
        await db.routes.delete_many({})
        print("Cleared existing data")
        
        print("Creating route connections...")
        connections = await create_comprehensive_connections()
        
        print("Inserting stops with connections...")
        stops_to_insert = []
        for stop in COMPREHENSIVE_STOPS:
            stop_doc = {
                "stop_id": stop["stop_id"],
                "name": stop["name"],
                "location": {
                    "type": "Point",
                    "coordinates": [stop["lon"], stop["lat"]]  # GeoJSON format
                },
                "connections": connections.get(stop["stop_id"], []),
                "zone": stop.get("zone", "unknown")
            }
            stops_to_insert.append(stop_doc)
        
        await db.stops.insert_many(stops_to_insert)
        print(f"Inserted {len(stops_to_insert)} stops")
        
        print("Inserting routes...")
        await db.routes.insert_many(COMPREHENSIVE_ROUTES)
        print(f"Inserted {len(COMPREHENSIVE_ROUTES)} routes")
        
        print("Creating database indexes...")
        await db.stops.create_index([("location", "2dsphere")])
        await db.stops.create_index("stop_id", unique=True)
        await db.routes.create_index("route_id", unique=True)
        await db.stops.create_index("zone")
        print("Created indexes")
        
        # Print statistics
        total_connections = sum(len(conns) for conns in connections.values())
        metro_stops = len([s for s in COMPREHENSIVE_STOPS if s["stop_id"].startswith(("M", "P"))])
        bus_stops = len([s for s in COMPREHENSIVE_STOPS if s["stop_id"].startswith("B")])
        tech_stops = len([s for s in COMPREHENSIVE_STOPS if s["stop_id"].startswith("T")])
        
        print(f"""
Comprehensive data loaded successfully!

Network Statistics:
   - Total Stops: {len(COMPREHENSIVE_STOPS)}
     - Metro Stops: {metro_stops}
     - Bus Stops: {bus_stops} 
     - Tech Hubs: {tech_stops}
   - Total Routes: {len(COMPREHENSIVE_ROUTES)}
   - Total Connections: {total_connections}
   - Coverage: Multi-modal transit network
   
Metro Lines: 2 (Red & Purple)
Bus Routes: {len([r for r in COMPREHENSIVE_ROUTES if r['route_type'] == 'bus'])}
Tech Park Coverage: Whitefield, ORR, Central Bangalore

This network now supports realistic journey planning across Bangalore!
        """)
        
    except Exception as e:
        print(f"Error loading comprehensive data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if should_close and client:
            client.close()


if __name__ == "__main__":
    asyncio.run(load_comprehensive_data())