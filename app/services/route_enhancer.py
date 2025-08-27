"""
Route Enhancement Service
Adds additional features like walking directions, environmental impact, calories, etc.
"""
from typing import List, Optional, Tuple
from geopy.distance import geodesic
import math

from app.models.route import OptimizedRoute, RouteSegment, WalkingDirection
from app.services.graph_service import graph_service


class RouteEnhancer:
    """Enhances routes with additional metadata and features"""
    
    def __init__(self):
        # Average speeds in km/h
        self.WALKING_SPEED = 5.0
        self.BUS_SPEED = 20.0
        self.METRO_SPEED = 35.0
        
        # Environmental factors
        self.CO2_SAVED_PER_KM = 0.21  # kg CO2 saved per km vs private car
        self.CALORIES_PER_WALKING_MINUTE = 4.0  # calories burned per minute walking
        
    def enhance_route(
        self, 
        route: OptimizedRoute, 
        start_lat: float, 
        start_lon: float,
        end_lat: float, 
        end_lon: float
    ) -> OptimizedRoute:
        """Add enhanced features to a route"""
        
        # Generate route summary
        route.route_summary = self._generate_route_summary(route)
        
        # Calculate environmental impact
        route.co2_saved_kg = self._calculate_co2_saved(route)
        
        # Calculate calories burned
        route.calories_burned = self._calculate_calories_burned(route)
        
        # Add walking directions for start and end
        route = self._add_walking_directions(route, start_lat, start_lon, end_lat, end_lon)
        
        # Enhance individual segments
        route.segments = [self._enhance_segment(seg) for seg in route.segments]
        
        return route
    
    def _generate_route_summary(self, route: OptimizedRoute) -> str:
        """Generate a human-readable route summary"""
        if not route.segments:
            return "No route found"
        
        summary_parts = []
        
        # Walking to start
        if route.start_walking_time > 0:
            summary_parts.append(f"Walk {route.start_walking_time}min to {route.segments[0].from_stop_name}")
        
        # Transit segments
        current_route = None
        segment_count = 0
        
        for segment in route.segments:
            if segment.route_id != current_route:
                if current_route is not None:
                    # Add previous route summary
                    route_type = "metro" if "METRO" in current_route else "bus"
                    summary_parts.append(f"Take {route_type} {current_route} for {segment_count} stops")
                
                current_route = segment.route_id
                segment_count = 1
            else:
                segment_count += 1
        
        # Add final route
        if current_route:
            route_type = "metro" if "METRO" in current_route else "bus"
            summary_parts.append(f"Take {route_type} {current_route} for {segment_count} stops")
        
        # Walking from end
        if route.end_walking_time > 0:
            summary_parts.append(f"Walk {route.end_walking_time}min to destination")
        
        return " → ".join(summary_parts)
    
    def _calculate_co2_saved(self, route: OptimizedRoute) -> float:
        """Calculate CO2 saved by using public transport vs private car"""
        total_distance = route.total_distance_km
        
        # Add distance for all transit segments
        for segment in route.segments:
            if segment.route_type in ["bus", "metro"]:
                # Estimate segment distance based on time and mode
                if segment.route_type == "metro":
                    segment_distance = (segment.time - 1) * (self.METRO_SPEED / 60)  # -1 for station stop
                else:
                    segment_distance = (segment.time - 2) * (self.BUS_SPEED / 60)  # -2 for traffic/stops
                total_distance += max(0, segment_distance)
        
        return round(total_distance * self.CO2_SAVED_PER_KM, 2)
    
    def _calculate_calories_burned(self, route: OptimizedRoute) -> int:
        """Calculate calories burned during walking portions"""
        walking_minutes = route.walking_time
        return int(walking_minutes * self.CALORIES_PER_WALKING_MINUTE)
    
    def _add_walking_directions(
        self, 
        route: OptimizedRoute, 
        start_lat: float, 
        start_lon: float,
        end_lat: float, 
        end_lon: float
    ) -> OptimizedRoute:
        """Add walking directions for start and end of journey"""
        
        if route.segments:
            # Walking to first stop
            first_stop_id = route.segments[0].from_stop
            if first_stop_id in graph_service.stops_cache:
                first_stop = graph_service.stops_cache[first_stop_id]
                start_walking_time, start_distance = graph_service.calculate_walking_time_from_coords(
                    start_lat, start_lon, first_stop_id
                )
                route.start_walking_time = start_walking_time
                
                # Generate walking direction
                if start_walking_time > 0:
                    direction = self._generate_walking_direction(
                        start_lat, start_lon,
                        first_stop.location.coordinates[1], first_stop.location.coordinates[0],
                        f"Walk to {first_stop.name}"
                    )
                    
                    # Add as first segment if it's a walking segment
                    walking_segment = RouteSegment(
                        route_id="WALKING",
                        route_name="Walking",
                        route_type="walking",
                        from_stop="START",
                        to_stop=first_stop_id,
                        from_stop_name="Your Location",
                        to_stop_name=first_stop.name,
                        time=start_walking_time,
                        cost=0.0,
                        sequence_start=0,
                        sequence_end=1,
                        walking_directions=[direction]
                    )
                    route.segments.insert(0, walking_segment)
            
            # Walking from last stop
            last_stop_id = route.segments[-1].to_stop
            if last_stop_id in graph_service.stops_cache:
                last_stop = graph_service.stops_cache[last_stop_id]
                end_walking_time, end_distance = graph_service.calculate_walking_time_from_coords(
                    end_lat, end_lon, last_stop_id
                )
                route.end_walking_time = end_walking_time
                
                # Generate walking direction
                if end_walking_time > 0:
                    direction = self._generate_walking_direction(
                        last_stop.location.coordinates[1], last_stop.location.coordinates[0],
                        end_lat, end_lon,
                        f"Walk to destination"
                    )
                    
                    # Add as last segment
                    walking_segment = RouteSegment(
                        route_id="WALKING",
                        route_name="Walking",
                        route_type="walking", 
                        from_stop=last_stop_id,
                        to_stop="END",
                        from_stop_name=last_stop.name,
                        to_stop_name="Your Destination",
                        time=end_walking_time,
                        cost=0.0,
                        sequence_start=len(route.segments),
                        sequence_end=len(route.segments) + 1,
                        walking_directions=[direction]
                    )
                    route.segments.append(walking_segment)
        
        return route
    
    def _generate_walking_direction(
        self, 
        from_lat: float, 
        from_lon: float,
        to_lat: float, 
        to_lon: float,
        instruction: str
    ) -> WalkingDirection:
        """Generate a walking direction between two points"""
        
        distance_km = geodesic((from_lat, from_lon), (to_lat, to_lon)).kilometers
        distance_meters = int(distance_km * 1000)
        duration_seconds = int((distance_km / self.WALKING_SPEED) * 3600)
        
        # Generate basic direction instruction
        bearing = self._calculate_bearing(from_lat, from_lon, to_lat, to_lon)
        direction = self._bearing_to_direction(bearing)
        
        full_instruction = f"{instruction} ({direction}, {distance_meters}m)"
        
        return WalkingDirection(
            instruction=full_instruction,
            distance_meters=distance_meters,
            duration_seconds=duration_seconds
        )
    
    def _enhance_segment(self, segment: RouteSegment) -> RouteSegment:
        """Add enhanced information to a segment"""
        
        # Add route type based on route_id
        if "METRO" in segment.route_id:
            segment.route_type = "metro"
        elif segment.route_id == "WALKING":
            segment.route_type = "walking"
        else:
            segment.route_type = "bus"
        
        return segment
    
    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate bearing between two points"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lon_rad = math.radians(lon2 - lon1)
        
        y = math.sin(delta_lon_rad) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon_rad))
        
        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)
        
        return (bearing_deg + 360) % 360
    
    def _bearing_to_direction(self, bearing: float) -> str:
        """Convert bearing to cardinal direction"""
        directions = ["North", "Northeast", "East", "Southeast", 
                     "South", "Southwest", "West", "Northwest", "North"]
        index = int((bearing + 22.5) / 45)
        return directions[index]


# Global instance
route_enhancer = RouteEnhancer()