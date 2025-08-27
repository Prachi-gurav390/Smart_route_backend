"""
GTFS (General Transit Feed Specification) parser
"""
import pandas as pd
import os
import asyncio
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GTFSParser:
    def __init__(self, gtfs_path: str):
        self.gtfs_path = gtfs_path
        self.stops_df = None
        self.routes_df = None
        self.stop_times_df = None
        self.trips_df = None
    
    def load_gtfs_files(self):
        """Load GTFS files into pandas DataFrames"""
        try:
            # Required files
            self.stops_df = pd.read_csv(os.path.join(self.gtfs_path, 'stops.txt'))
            self.routes_df = pd.read_csv(os.path.join(self.gtfs_path, 'routes.txt'))
            self.stop_times_df = pd.read_csv(os.path.join(self.gtfs_path, 'stop_times.txt'))
            self.trips_df = pd.read_csv(os.path.join(self.gtfs_path, 'trips.txt'))
            
            logger.info(f"Loaded GTFS files:")
            logger.info(f"  - Stops: {len(self.stops_df)}")
            logger.info(f"  - Routes: {len(self.routes_df)}")
            logger.info(f"  - Stop times: {len(self.stop_times_df)}")
            logger.info(f"  - Trips: {len(self.trips_df)}")
            
        except Exception as e:
            logger.error(f"Error loading GTFS files: {e}")
            raise
    
    def process_data(self):
        """Process GTFS data and create connections"""
        # Merge data to get route information for each trip
        merged_df = self.stop_times_df.merge(
            self.trips_df[['trip_id', 'route_id']], 
            on='trip_id'
        )
        
        # Sort by trip and stop sequence
        merged_df = merged_df.sort_values(['trip_id', 'stop_sequence'])
        
        # Create connections between consecutive stops
        connections = {}
        
        for trip_id, trip_group in merged_df.groupby('trip_id'):
            trip_stops = trip_group.sort_values('stop_sequence')
            route_id = trip_stops.iloc[0]['route_id']
            
            for i in range(len(trip_stops) - 1):
                current_stop = trip_stops.iloc[i]
                next_stop = trip_stops.iloc[i + 1]
                
                from_stop_id = str(current_stop['stop_id'])
                to_stop_id = str(next_stop['stop_id'])
                
                # Calculate travel time (simplified)
                time_diff = self._calculate_time_diff(
                    current_stop.get('departure_time', '00:00:00'),
                    next_stop.get('arrival_time', '00:00:00')
                )
                
                if from_stop_id not in connections:
                    connections[from_stop_id] = []
                
                # Estimate cost based on route type
                route_type = self._get_route_type(route_id)
                estimated_cost = self._estimate_cost(route_type, time_diff)
                
                connections[from_stop_id].append({
                    "to_stop_id": to_stop_id,
                    "route_id": str(route_id),
                    "time": max(1, time_diff),  # Minimum 1 minute
                    "cost": estimated_cost,
                    "sequence": int(current_stop['stop_sequence'])
                })
        
        return connections
    
    def _calculate_time_diff(self, departure_time: str, arrival_time: str) -> int:
        """Calculate time difference in minutes"""
        try:
            def time_to_minutes(time_str):
                if pd.isna(time_str):
                    return 0
                parts = str(time_str).split(':')
                return int(parts[0]) * 60 + int(parts[1])
            
            dep_minutes = time_to_minutes(departure_time)
            arr_minutes = time_to_minutes(arrival_time)
            
            diff = arr_minutes - dep_minutes
            if diff < 0:  # Handle day overflow
                diff += 24 * 60
            
            return max(1, diff)  # Minimum 1 minute
            
        except:
            return 5  # Default to 5 minutes
    
    def _get_route_type(self, route_id: str) -> str:
        """Get route type from routes dataframe"""
        route_info = self.routes_df[self.routes_df['route_id'] == route_id]
        if not route_info.empty:
            route_type = route_info.iloc[0].get('route_type', 3)
            # GTFS route types: 0=Tram, 1=Metro, 2=Rail, 3=Bus, etc.
            type_mapping = {0: 'tram', 1: 'metro', 2: 'rail', 3: 'bus'}
            return type_mapping.get(route_type, 'bus')
        return 'bus'
    
    def _estimate_cost(self, route_type: str, time_minutes: int) -> float:
        """Estimate cost based on route type and time"""
        base_costs = {
            'metro': 2.0,
            'rail': 3.0,
            'bus': 1.5,
            'tram': 1.8
        }
        base_cost = base_costs.get(route_type, 1.5)
        
        # Add cost based on time (longer trips cost more)
        time_cost = (time_minutes / 10) * 0.5
        return round(base_cost + time_cost, 2)
    
    async def load_to_database(self):
        """Load processed data to MongoDB"""
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        
        try:
            # Process connections
            connections = self.process_data()
            
            # Prepare stops data
            stops_to_insert = []
            for _, stop in self.stops_df.iterrows():
                stop_doc = {
                    "stop_id": str(stop['stop_id']),
                    "name": str(stop['stop_name']),
                    "location": {
                        "type": "Point",
                        "coordinates": [float(stop['stop_lon']), float(stop['stop_lat'])]
                    },
                    "connections": connections.get(str(stop['stop_id']), [])
                }
                stops_to_insert.append(stop_doc)
            
            # Prepare routes data
            routes_to_insert = []
            for _, route in self.routes_df.iterrows():
                # Get stops for this route
                route_trips = self.trips_df[self.trips_df['route_id'] == route['route_id']]
                if not route_trips.empty:
                    # Get stops from first trip (assuming similar stop patterns)
                    first_trip = route_trips.iloc[0]['trip_id']
                    trip_stops = self.stop_times_df[
                        self.stop_times_df['trip_id'] == first_trip
                    ].sort_values('stop_sequence')
                    
                    route_doc = {
                        "route_id": str(route['route_id']),
                        "name": str(route['route_short_name']),
                        "stops": [str(stop_id) for stop_id in trip_stops['stop_id'].tolist()],
                        "route_type": self._get_route_type(route['route_id'])
                    }
                    routes_to_insert.append(route_doc)
            
            # Clear existing data
            await db.stops.delete_many({})
            await db.routes.delete_many({})
            logger.info("Cleared existing data")
            
            # Insert new data
            if stops_to_insert:
                await db.stops.insert_many(stops_to_insert)
                logger.info(f"Inserted {len(stops_to_insert)} stops")
            
            if routes_to_insert:
                await db.routes.insert_many(routes_to_insert)
                logger.info(f"Inserted {len(routes_to_insert)} routes")
            
            # Create indexes
            await db.stops.create_index([("location", "2dsphere")])
            await db.stops.create_index("stop_id", unique=True)
            await db.routes.create_index("route_id", unique=True)
            logger.info("Created indexes")
            
            logger.info("GTFS data loaded successfully!")
            
        except Exception as e:
            logger.error(f"Error loading to database: {e}")
            raise
        finally:
            client.close()

async def main():
    """Main function to run GTFS parser"""
    gtfs_path = input("Enter path to GTFS data directory: ").strip()
    
    if not os.path.exists(gtfs_path):
        print(f"Directory {gtfs_path} does not exist")
        return
    
    parser = GTFSParser(gtfs_path)
    
    try:
        parser.load_gtfs_files()
        await parser.load_to_database()
        print("GTFS data processing completed successfully!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())