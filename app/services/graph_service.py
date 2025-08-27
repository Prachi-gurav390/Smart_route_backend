import heapq
import math
import itertools
from typing import Dict, List, Tuple, Optional, Set
from geopy.distance import geodesic
import logging
from app.database import get_database
from app.models.stop import Stop, Connection
from app.models.route import RouteSegment, OptimizedRoute
from app.config import settings
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GraphService:
    def __init__(self):
        self.stops_cache: Dict[str, Stop] = {}
        self.routes_cache: Dict[str, dict] = {}

    async def load_graph_data(self):
        """Load and cache graph data from database"""
        try:
            db = await get_database()
            if db is None:
                logger.error("Database not available for loading graph data")
                return

            # Load stops
            self.stops_cache.clear()
            async for stop_doc in db.stops.find():
                stop = Stop(**stop_doc)
                self.stops_cache[stop.stop_id] = stop

            # Load routes
            self.routes_cache.clear()
            async for route_doc in db.routes.find():
                self.routes_cache[route_doc["route_id"]] = route_doc

            logger.info(
                f"Graph data loaded: {len(self.stops_cache)} stops, {len(self.routes_cache)} routes")
        except Exception as e:
            logger.error(f"Error loading graph data: {e}")
            # Initialize empty caches to prevent NoneType errors
            self.stops_cache = {}
            self.routes_cache = {}

    def get_stop_coordinates(self, stop_id: str) -> Tuple[float, float]:
        """Get latitude, longitude for a stop"""
        if stop_id in self.stops_cache:
            coords = self.stops_cache[stop_id].location.coordinates
            return coords[1], coords[0]  # lat, lon (GeoJSON is [lon, lat])
        return None, None

    def validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """Validate if coordinates are reasonable"""
        # Basic coordinate range validation
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return False

        # Check if coordinates are within reasonable distance of any stop
        if self.stops_cache:
            min_distance = float('inf')
            for stop in self.stops_cache.values():
                stop_coords = (
                    stop.location.coordinates[1], stop.location.coordinates[0])
                distance = geodesic((latitude, longitude),
                                    stop_coords).kilometers
                min_distance = min(min_distance, distance)

            # Reject coordinates more than configured distance from any stop
            return min_distance <= settings.MAX_SEARCH_RADIUS_KM

        return True

    def calculate_walking_time_from_coords(self, lat: float, lon: float, stop_id: str) -> Tuple[int, float]:
        """Calculate walking time and distance from coordinates to stop"""
        stop_coords = self.get_stop_coordinates(stop_id)

        if not stop_coords:
            return float('inf'), 0.0

        distance_km = geodesic((lat, lon), stop_coords).kilometers

        if distance_km > settings.MAX_WALKING_DISTANCE_KM:
            return float('inf'), distance_km

        walking_time_minutes = (distance_km / settings.WALKING_SPEED_KMH) * 60
        return int(walking_time_minutes), distance_km

    def calculate_walking_time(self, stop1_id: str, stop2_id: str) -> int:
        """Calculate walking time between two stops in minutes"""
        coords1 = self.get_stop_coordinates(stop1_id)
        coords2 = self.get_stop_coordinates(stop2_id)

        if not coords1 or not coords2:
            return float('inf')

        distance_km = geodesic(coords1, coords2).kilometers

        if distance_km > settings.MAX_WALKING_DISTANCE_KM:
            return float('inf')

        walking_time_minutes = (distance_km / settings.WALKING_SPEED_KMH) * 60
        return int(walking_time_minutes)

    def find_nearest_stops(self, latitude: float, longitude: float, limit: int = 5) -> List[Tuple[str, float]]:
        """Find nearest stops to given coordinates with distances"""
        distances = []

        logger.debug(f"Finding nearest stops to ({latitude}, {longitude})")

        for stop_id, stop in self.stops_cache.items():
            # MongoDB stores [longitude, latitude]
            stop_coords = (
                stop.location.coordinates[1], stop.location.coordinates[0])
            distance = geodesic((latitude, longitude), stop_coords).kilometers

            # Only include stops within maximum walking distance
            if distance <= settings.MAX_WALKING_DISTANCE_KM:
                distances.append((distance, stop_id, stop.name))

        distances.sort()

        logger.debug(
            f"Found {len(distances)} stops within {settings.MAX_WALKING_DISTANCE_KM}km")
        for i in range(min(limit, len(distances))):
            dist, stop_id, name = distances[i]
            logger.debug(f"  {i+1}. {stop_id} ({name}) - {dist:.3f}km")

        return [(stop_id, dist) for dist, stop_id, _ in distances[:limit]]

    def get_mode_specific_penalties(self, route_id: str) -> Tuple[int, int]:
        """Get boarding time and transfer penalties based on route type"""
        route_info = self.routes_cache.get(route_id, {})
        route_type = route_info.get("route_type", "bus")

        if route_type == "metro":
            return settings.METRO_BOARDING_TIME, settings.TRANSFER_WALKING_TIME
        else:  # bus or other
            return settings.BUS_BOARDING_TIME, settings.TRANSFER_WALKING_TIME

    async def find_optimal_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        optimize_for: str = "time"
    ) -> Optional[OptimizedRoute]:
        """
        Find optimal route using enhanced Dijkstra's algorithm with realistic transit features
        """
        if not self.stops_cache:
            await self.load_graph_data()

        logger.info(
            f"Finding route from ({start_lat}, {start_lon}) to ({end_lat}, {end_lon}) "
            f"optimized for {optimize_for}")

        # Validate coordinates
        if not self.validate_coordinates(start_lat, start_lon):
            logger.error(
                f"Invalid start coordinates: ({start_lat}, {start_lon})")
            return None

        if not self.validate_coordinates(end_lat, end_lon):
            logger.error(f"Invalid end coordinates: ({end_lat}, {end_lon})")
            return None

        # Find nearest stops to start and end with distances
        start_stops_with_dist = self.find_nearest_stops(
            start_lat, start_lon, 3)
        end_stops_with_dist = self.find_nearest_stops(end_lat, end_lon, 3)

        if not start_stops_with_dist or not end_stops_with_dist:
            logger.error("No nearby stops found within walking distance")
            return None

        start_stops = [stop_id for stop_id, _ in start_stops_with_dist]
        end_stops = [stop_id for stop_id, _ in end_stops_with_dist]

        logger.debug(f"Start stops: {start_stops}")
        logger.debug(f"End stops: {end_stops}")

        best_route = None
        best_cost = float('inf')

        # Try all combinations of start and end stops
        for i, start_stop in enumerate(start_stops):
            for j, end_stop in enumerate(end_stops):
                logger.debug(f"Trying route: {start_stop} → {end_stop}")
                route = await self._dijkstra_with_transfers(start_stop, end_stop, optimize_for)
                if route:
                    # Add walking times and distances
                    start_walking_time, start_walking_dist = self.calculate_walking_time_from_coords(
                        start_lat, start_lon, start_stop)
                    end_walking_time, end_walking_dist = self.calculate_walking_time_from_coords(
                        end_lat, end_lon, end_stop)

                    route.walking_time = start_walking_time + end_walking_time
                    route.total_distance_km = start_walking_dist + end_walking_dist
                    route.total_time += route.walking_time

                    route_cost = self._calculate_total_cost(
                        route, optimize_for)
                    logger.debug(f"Found route with cost: {route_cost}")

                    if route_cost < best_cost:
                        best_route = route
                        best_cost = route_cost
                else:
                    logger.debug("No route found")

        if best_route:
            logger.info(f"Best route found: {' → '.join(best_route.path)} "
                        f"(Total time: {best_route.total_time}min, Walking: {best_route.walking_time}min)")
        else:
            logger.warning(
                "No route found between any start/end stop combinations")

        return best_route

    async def _dijkstra_with_transfers(
        self,
        start_stop_id: str,
        end_stop_id: str,
        optimize_for: str
    ) -> Optional[OptimizedRoute]:
        """
        Find optimal route using proper Dijkstra's algorithm with transfers
        """
        if start_stop_id not in self.stops_cache or end_stop_id not in self.stops_cache:
            return None

        # Handle same start and end stop
        if start_stop_id == end_stop_id:
            return OptimizedRoute(
                path=[start_stop_id],
                segments=[],
                total_time=0,
                total_cost=0.0,
                transfers=0,
                walking_time=0,
                total_distance_km=0.0,
                start_walking_time=0,
                end_walking_time=0,
                route_summary="Already at destination",
                alternative_routes_count=0,
                co2_saved_kg=0.0,
                calories_burned=0
            )

        start_stop = self.stops_cache[start_stop_id]
        end_stop = self.stops_cache[end_stop_id]

        # Method 1: Try direct connections if they exist
        for connection in start_stop.connections:
            if connection.to_stop_id == end_stop_id:
                return self._create_route_from_connection(connection, start_stop, end_stop)

        # Method 2: Find routes that serve both stops
        route_match = await self._find_route_serving_both_stops(start_stop_id, end_stop_id)
        if route_match:
            return route_match

        # Method 3: Use proper Dijkstra to find multi-hop routes
        logger.info(f"No direct route found, using Dijkstra for {start_stop_id} -> {end_stop_id}")
        dijkstra_route = self._dijkstra_pathfinding(start_stop_id, end_stop_id, optimize_for)
        if dijkstra_route:
            return dijkstra_route

        # Method 4: No route found - return None instead of creating fake routes
        logger.warning(f"No route found between {start_stop_id} and {end_stop_id}")
        return None

    def _dijkstra_pathfinding(
        self,
        start_stop_id: str,
        end_stop_id: str,
        optimize_for: str,
        max_transfers: int = 5
    ) -> Optional[OptimizedRoute]:
        """
        Proper Dijkstra pathfinding with transfers support
        """
        # Counter to ensure unique priorities and avoid comparison issues
        counter = itertools.count()
        
        # Priority queue: (cost, counter, current_stop, path, segments, transfers, total_time, total_cost)
        pq = [(0, next(counter), start_stop_id, [start_stop_id], [], 0, 0, 0.0)]
        # Track best cost to each stop to avoid revisiting with worse cost
        best_costs = {start_stop_id: 0}
        
        while pq:
            current_cost, _, current_stop, path, segments, transfers, total_time, total_cost = heapq.heappop(pq)
            
            # Skip if we've found a better path to this stop already
            if current_stop in best_costs and current_cost > best_costs[current_stop]:
                continue
            
            # Found destination
            if current_stop == end_stop_id:
                logger.info(f"Found path: {' -> '.join(path)} with {transfers} transfers")
                
                return OptimizedRoute(
                    path=path,
                    segments=segments,
                    total_time=total_time,
                    total_cost=total_cost,
                    transfers=transfers,
                    walking_time=0,
                    total_distance_km=0.0,
                    start_walking_time=0,
                    end_walking_time=0,
                    route_summary=f"Route with {len(segments)} segments, {transfers} transfers",
                    alternative_routes_count=0,
                    co2_saved_kg=total_time * 0.1,
                    calories_burned=0
                )
            
            # Skip if too many transfers
            if transfers >= max_transfers:
                continue
                
            # Explore connections from current stop
            if current_stop in self.stops_cache:
                current_stop_obj = self.stops_cache[current_stop]
                
                for connection in current_stop_obj.connections:
                    next_stop = connection.to_stop_id
                    
                    # Skip if already in path (avoid cycles)
                    if next_stop in path:
                        continue
                        
                    # Calculate costs
                    segment_time = connection.time
                    segment_cost = connection.cost
                    
                    # Add boarding time for first segment or if changing routes
                    boarding_penalty = 0
                    is_transfer = False
                    
                    if len(segments) == 0:
                        # First segment - add boarding time
                        boarding_time, _ = self.get_mode_specific_penalties(connection.route_id)
                        boarding_penalty = boarding_time
                    elif segments[-1].route_id != connection.route_id:
                        # Route change - this is a transfer
                        boarding_time, transfer_time = self.get_mode_specific_penalties(connection.route_id)
                        boarding_penalty = boarding_time + transfer_time
                        is_transfer = True
                    
                    new_time = total_time + segment_time + boarding_penalty
                    new_cost = total_cost + segment_cost
                    new_transfers = transfers + (1 if is_transfer else 0)
                    
                    # Calculate priority based on optimization criteria
                    if optimize_for == "time":
                        priority = new_time
                    elif optimize_for == "cost":
                        priority = new_cost
                    else:  # transfers
                        priority = new_transfers * 100 + new_time
                    
                    # Create segment
                    current_stop_name = self.stops_cache[current_stop].name
                    next_stop_name = self.stops_cache[next_stop].name
                    route_info = self.routes_cache.get(connection.route_id, {})
                    
                    segment = RouteSegment(
                        route_id=connection.route_id,
                        route_name=route_info.get("route_long_name", f"Route {connection.route_id}"),
                        route_type=route_info.get("route_type", "bus"),
                        from_stop=current_stop,
                        to_stop=next_stop,
                        from_stop_name=current_stop_name,
                        to_stop_name=next_stop_name,
                        time=segment_time,
                        cost=segment_cost,
                        sequence_start=connection.sequence,
                        sequence_end=connection.sequence + 1,
                        boarding_time=boarding_penalty,
                        transfer_time=0,
                        walking_directions=[]
                    )
                    
                    new_path = path + [next_stop]
                    new_segments = segments + [segment]
                    
                    # Only add to queue if we found a better path to this stop
                    if next_stop not in best_costs or priority < best_costs[next_stop]:
                        best_costs[next_stop] = priority
                        heapq.heappush(pq, (
                            priority, next(counter), next_stop, new_path, new_segments,
                            new_transfers, new_time, new_cost
                        ))
        
        logger.info(f"No path found between {start_stop_id} and {end_stop_id}")
        return None

    def _create_route_from_connection(self, connection, start_stop, end_stop):
        """Create route from existing connection data"""
        from app.models.route import RouteSegment, OptimizedRoute
        
        route_info = self.routes_cache.get(connection.route_id, {})
        route_name = route_info.get("route_long_name", f"Route {connection.route_id}")
        route_type = route_info.get("route_type", "metro")
        
        segment = RouteSegment(
            route_id=connection.route_id,
            route_name=route_name,
            route_type=route_type,
            from_stop=start_stop.stop_id,
            to_stop=end_stop.stop_id,
            from_stop_name=start_stop.name,
            to_stop_name=end_stop.name,
            time=connection.time,
            cost=connection.cost,
            sequence_start=1,
            sequence_end=2,
            boarding_time=self.get_mode_specific_penalties(connection.route_id)[0],
            transfer_time=0,
            walking_directions=[]
        )

        return OptimizedRoute(
            path=[start_stop.stop_id, end_stop.stop_id],
            segments=[segment],
            total_time=connection.time + segment.boarding_time,
            total_cost=connection.cost,
            transfers=0,
            walking_time=0,
            total_distance_km=0.0,
            start_walking_time=0,
            end_walking_time=0,
            route_summary=f"Take {route_type} {connection.route_id} direct",
            alternative_routes_count=0,
            co2_saved_kg=0.0,
            calories_burned=0
        )

    async def _find_route_serving_both_stops(self, start_stop_id: str, end_stop_id: str):
        """Find a route that serves both stops by analyzing route data"""
        db = await get_database()
        
        # Find routes that contain both stops
        pipeline = [
            {"$match": {"stops": {"$all": [start_stop_id, end_stop_id]}}},
            {"$limit": 1}
        ]
        
        async for route_doc in db.routes.aggregate(pipeline):
            route_id = route_doc["route_id"]
            stops_list = route_doc.get("stops", [])
            
            try:
                start_idx = stops_list.index(start_stop_id)
                end_idx = stops_list.index(end_stop_id)
                
                # Calculate travel details
                stops_between = abs(end_idx - start_idx)
                travel_time = stops_between * 3  # 3 minutes per stop
                travel_cost = stops_between * 2.0  # 2 units per stop
                
                return self._create_route_from_data(
                    route_id, route_doc, start_stop_id, end_stop_id, 
                    travel_time, travel_cost, stops_between
                )
            except ValueError:
                continue
                
        return None

    def _create_route_from_data(self, route_id, route_doc, start_stop_id, end_stop_id, 
                               travel_time, travel_cost, stops_between):
        """Create route from route document data"""
        from app.models.route import RouteSegment, OptimizedRoute
        
        start_stop = self.stops_cache[start_stop_id]
        end_stop = self.stops_cache[end_stop_id]
        
        route_name = route_doc.get("route_long_name", f"Route {route_id}")
        route_type = route_doc.get("route_type", "metro")
        
        boarding_time, _ = self.get_mode_specific_penalties(route_id)
        
        segment = RouteSegment(
            route_id=route_id,
            route_name=route_name,
            route_type=route_type,
            from_stop=start_stop_id,
            to_stop=end_stop_id,
            from_stop_name=start_stop.name,
            to_stop_name=end_stop.name,
            time=travel_time,
            cost=travel_cost,
            sequence_start=1,
            sequence_end=stops_between + 1,
            boarding_time=boarding_time,
            transfer_time=0,
            walking_directions=[]
        )

        return OptimizedRoute(
            path=[start_stop_id, end_stop_id],
            segments=[segment],
            total_time=travel_time + boarding_time,
            total_cost=travel_cost,
            transfers=0,
            walking_time=0,
            total_distance_km=0.0,
            start_walking_time=0,
            end_walking_time=0,
            route_summary=f"Take {route_type} {route_name} for {stops_between} stops",
            alternative_routes_count=0,
            co2_saved_kg=2.5,
            calories_burned=0
        )

    def _create_fallback_metro_route(self, start_stop, end_stop):
        """Create a reasonable metro route as fallback"""
        from app.models.route import RouteSegment, OptimizedRoute
        
        # Calculate distance-based estimates
        start_coords = (start_stop.location.coordinates[1], start_stop.location.coordinates[0])
        end_coords = (end_stop.location.coordinates[1], end_stop.location.coordinates[0])
        
        distance_km = geodesic(start_coords, end_coords).kilometers
        
        # Reasonable metro estimates
        travel_time = max(5, int(distance_km * 4))  # ~4 minutes per km for metro
        travel_cost = max(10.0, distance_km * 8)   # ~8 units per km
        
        # Infer route from stop IDs (M002 -> M006 suggests Purple Line)
        route_id = "PURPLE_LINE"
        route_name = "Purple Line"
        
        segment = RouteSegment(
            route_id=route_id,
            route_name=route_name,
            route_type="metro",
            from_stop=start_stop.stop_id,
            to_stop=end_stop.stop_id,
            from_stop_name=start_stop.name,
            to_stop_name=end_stop.name,
            time=travel_time,
            cost=travel_cost,
            sequence_start=1,
            sequence_end=2,
            boarding_time=1,
            transfer_time=0,
            walking_directions=[]
        )

        return OptimizedRoute(
            path=[start_stop.stop_id, end_stop.stop_id],
            segments=[segment],
            total_time=travel_time + 1,
            total_cost=travel_cost,
            transfers=0,
            walking_time=0,
            total_distance_km=distance_km,
            start_walking_time=0,
            end_walking_time=0,
            route_summary=f"Take metro {route_name} direct",
            alternative_routes_count=0,
            co2_saved_kg=round(distance_km * 0.5, 2),
            calories_burned=0
        )

    def _calculate_total_cost(self, route: OptimizedRoute, optimize_for: str) -> float:
        """Calculate total cost for comparison including walking time"""
        if optimize_for == "time":
            return route.total_time + route.walking_time
        elif optimize_for == "cost":
            return route.total_cost
        else:  # transfers
            return route.transfers

    async def get_algorithm_execution_steps(
        self,
        start_stop_id: str,
        end_stop_id: str,
        optimize_for: str
    ) -> List[Dict]:
        """
        Get step-by-step execution of Dijkstra's algorithm for visualization
        """
        if start_stop_id not in self.stops_cache or end_stop_id not in self.stops_cache:
            return []

        steps = []
        counter = itertools.count()
        
        # Priority queue: (cost, counter, current_stop, path, segments, transfers, total_time, total_cost)
        pq = [(0, next(counter), start_stop_id, [start_stop_id], [], 0, 0, 0.0)]
        visited = set()
        step_count = 0
        
        # Initial state
        steps.append({
            "step": step_count,
            "action": "initialize",
            "description": f"Initialize algorithm with start node: {start_stop_id}",
            "current_node": start_stop_id,
            "priority_queue": [{"node": start_stop_id, "cost": 0, "path": [start_stop_id]}],
            "visited": list(visited),
            "path": [start_stop_id],
            "found_destination": False
        })
        step_count += 1
        
        while pq and step_count < 100:  # Increased limit for visualization
            current_cost, _, current_stop, path, segments, transfers, total_time, total_cost = heapq.heappop(pq)
            
            # Skip if already visited
            if current_stop in visited:
                steps.append({
                    "step": step_count,
                    "action": "skip_visited",
                    "description": f"Node {current_stop} already visited, skipping",
                    "current_node": current_stop,
                    "priority_queue": [{"node": item[2], "cost": item[0], "path": item[3]} for item in pq[:5]],
                    "visited": list(visited),
                    "path": path,
                    "found_destination": False
                })
                step_count += 1
                continue
                
            visited.add(current_stop)
            
            # Check if destination found
            if current_stop == end_stop_id:
                steps.append({
                    "step": step_count,
                    "action": "found_destination",
                    "description": f"Destination {end_stop_id} found! Path: {' → '.join(path)}",
                    "current_node": current_stop,
                    "priority_queue": [],
                    "visited": list(visited),
                    "path": path,
                    "found_destination": True,
                    "final_path": path,
                    "total_cost": current_cost,
                    "segments_count": len(segments),
                    "transfers": transfers
                })
                break
            
            # Process current node
            steps.append({
                "step": step_count,
                "action": "process_node",
                "description": f"Processing node {current_stop}, exploring neighbors",
                "current_node": current_stop,
                "priority_queue": [{"node": item[2], "cost": item[0], "path": item[3]} for item in pq[:5]],
                "visited": list(visited),
                "path": path,
                "found_destination": False
            })
            step_count += 1
            
            # Explore neighbors
            if current_stop in self.stops_cache:
                current_stop_obj = self.stops_cache[current_stop]
                neighbors_added = []
                
                for connection in current_stop_obj.connections:
                    next_stop = connection.to_stop_id
                    
                    if next_stop in path:  # Avoid cycles
                        continue
                        
                    # Calculate costs
                    segment_time = connection.time
                    segment_cost = connection.cost
                    
                    # Add boarding time for first segment or if changing routes
                    boarding_penalty = 0
                    is_transfer = False
                    
                    if len(segments) == 0:
                        boarding_time, _ = self.get_mode_specific_penalties(connection.route_id)
                        boarding_penalty = boarding_time
                    elif segments[-1]["route_id"] != connection.route_id:
                        boarding_time, transfer_time = self.get_mode_specific_penalties(connection.route_id)
                        boarding_penalty = boarding_time + transfer_time
                        is_transfer = True
                    
                    new_time = total_time + segment_time + boarding_penalty
                    new_cost = total_cost + segment_cost
                    new_transfers = transfers + (1 if is_transfer else 0)
                    
                    # Calculate priority based on optimization criteria
                    if optimize_for == "time":
                        priority = new_time
                    elif optimize_for == "cost":
                        priority = new_cost
                    else:  # transfers
                        priority = new_transfers * 100 + new_time
                    
                    new_path = path + [next_stop]
                    
                    # Create dummy segment for tracking
                    current_stop_name = self.stops_cache[current_stop].name
                    next_stop_name = self.stops_cache[next_stop].name
                    
                    dummy_segment = {
                        "route_id": connection.route_id,
                        "from_stop": current_stop,
                        "to_stop": next_stop,
                        "time": segment_time,
                        "cost": segment_cost
                    }
                    
                    new_segments = segments + [dummy_segment]
                    
                    heapq.heappush(pq, (
                        priority, next(counter), next_stop, new_path, new_segments,
                        new_transfers, new_time, new_cost
                    ))
                    
                    neighbors_added.append({
                        "node": next_stop,
                        "cost": priority,
                        "via_route": connection.route_id
                    })
                
                if neighbors_added:
                    steps.append({
                        "step": step_count,
                        "action": "add_neighbors",
                        "description": f"Added {len(neighbors_added)} neighbors to priority queue",
                        "current_node": current_stop,
                        "neighbors_added": neighbors_added,
                        "priority_queue": [{"node": item[2], "cost": item[0], "path": item[3]} for item in pq[:5]],
                        "visited": list(visited),
                        "path": path,
                        "found_destination": False
                    })
                    step_count += 1
        
        # Check final state after loop ends
        if step_count >= 100:
            # If we hit the step limit, check if there are still nodes to explore
            if pq:
                # Still have nodes to explore - hit visualization limit
                steps.append({
                    "step": step_count,
                    "action": "max_steps_reached",
                    "description": "Maximum visualization steps reached - algorithm continues in background",
                    "current_node": current_stop if 'current_stop' in locals() else start_stop_id,
                    "priority_queue": [{"node": item[2], "cost": item[0]} for item in pq[:5]],
                    "visited": list(visited),
                    "path": path if 'path' in locals() else [start_stop_id],
                    "found_destination": False,
                    "note": "The actual pathfinding algorithm continues beyond this limit"
                })
            else:
                # No more nodes to explore - algorithm completed without finding route
                steps.append({
                    "step": step_count,
                    "action": "no_route_found",
                    "description": "Algorithm completed: All reachable nodes explored, no route to destination",
                    "current_node": current_stop if 'current_stop' in locals() else start_stop_id,
                    "priority_queue": [],
                    "visited": list(visited),
                    "path": path if 'path' in locals() else [start_stop_id],
                    "found_destination": False,
                    "no_route_available": True,
                    "note": f"Explored {len(visited)} nodes - destination is not reachable from start point"
                })
        elif not pq:
            # Loop ended because priority queue is empty (all reachable nodes explored)
            steps.append({
                "step": step_count,
                "action": "no_route_found",
                "description": "Algorithm completed: All reachable nodes explored, no route to destination",
                "current_node": current_stop if 'current_stop' in locals() else start_stop_id,
                "priority_queue": [],
                "visited": list(visited),
                "path": path if 'path' in locals() else [start_stop_id],
                "found_destination": False,
                "no_route_available": True,
                "note": f"Explored {len(visited)} nodes - destination is not reachable from start point"
            })
        
        return steps


# Global instance
graph_service = GraphService()
