# from typing import Optional, List, Dict
# import logging
# from app.services.graph_service import graph_service
# from app.models.route import OptimizedRoute
# from app.database import get_database

# logger = logging.getLogger(__name__)


# class RouteOptimizer:
#     def __init__(self):
#         self.cache: Dict[str, OptimizedRoute] = {}

#     async def find_route(
#         self,
#         start_lat: float,
#         start_lon: float,
#         end_lat: float,
#         end_lon: float,
#         optimize_for: str = "time"
#     ) -> Optional[OptimizedRoute]:
#         """
#         Find optimal route between two points
#         """
#         # Create cache key
#         cache_key = f"{start_lat},{start_lon}-{end_lat},{end_lon}-{optimize_for}"

#         # Check cache first
#         if cache_key in self.cache:
#             logger.info(f"Cache hit for route: {cache_key}")
#             return self.cache[cache_key]

#         # Find route using graph service
#         route = await graph_service.find_optimal_route(
#             start_lat, start_lon, end_lat, end_lon, optimize_for
#         )

#         # Cache result
#         if route:
#             self.cache[cache_key] = route
#             logger.info(
#                 f"Found route with {len(route.segments)} segments, {route.transfers} transfers")

#         return route

#     async def find_route_by_stops(
#         self,
#         start_stop_id: str,
#         end_stop_id: str,
#         optimize_for: str = "time"
#     ) -> Optional[OptimizedRoute]:
#         """
#         Find optimal route between two specific stops
#         """
#         if not graph_service.stops_cache:
#             await graph_service.load_graph_data()

#         if start_stop_id not in graph_service.stops_cache or end_stop_id not in graph_service.stops_cache:
#             return None

#         route = await graph_service._dijkstra_with_transfers(start_stop_id, end_stop_id, optimize_for)
#         return route

#     async def get_stop_suggestions(self, query: str, limit: int = 10) -> List[Dict]:
#         """
#         Get stop suggestions for autocomplete
#         """
#         db = await get_database()

#         # Case-insensitive regex search
#         cursor = db.stops.find(
#             {"name": {"$regex": query, "$options": "i"}},
#             {"stop_id": 1, "name": 1, "location": 1}
#         ).limit(limit)

#         suggestions = []
#         async for stop in cursor:
#             suggestions.append({
#                 "stop_id": stop["stop_id"],
#                 "name": stop["name"],
#                 "latitude": stop["location"]["coordinates"][1],
#                 "longitude": stop["location"]["coordinates"][0]
#             })

#         return suggestions


# # Global instance
# route_optimizer = RouteOptimizer()


from typing import Optional, List, Dict
import logging
from app.services.graph_service import graph_service
from app.services.route_enhancer import route_enhancer
from app.models.route import OptimizedRoute
from app.database import get_database

logger = logging.getLogger(__name__)


class RouteOptimizer:
    def __init__(self):
        self.cache: Dict[str, OptimizedRoute] = {}

    async def find_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        optimize_for: str = "time"
    ) -> Optional[OptimizedRoute]:
        """
        Find optimal route between two points
        """
        # Create cache key
        cache_key = f"{start_lat:.4f},{start_lon:.4f}-{end_lat:.4f},{end_lon:.4f}-{optimize_for}"

        # Check cache first
        if cache_key in self.cache:
            logger.info(f"Cache hit for route: {cache_key}")
            return self.cache[cache_key]

        # Find route using graph service
        route = await graph_service.find_optimal_route(
            start_lat, start_lon, end_lat, end_lon, optimize_for
        )

        # Enhance route with additional features
        if route:
            route = route_enhancer.enhance_route(route, start_lat, start_lon, end_lat, end_lon)
            
            # Cache enhanced result
            self.cache[cache_key] = route
            logger.info(
                f"Found route: {route.route_summary} "
                f"({len(route.segments)} segments, {route.transfers} transfers, "
                f"{route.total_time}min total, {route.walking_time}min walking)")

        return route

    async def find_route_by_stops(
        self,
        start_stop_id: str,
        end_stop_id: str,
        optimize_for: str = "time"
    ) -> Optional[OptimizedRoute]:
        """
        Find optimal route between two specific stops
        """
        if not graph_service.stops_cache:
            await graph_service.load_graph_data()

        if start_stop_id not in graph_service.stops_cache or end_stop_id not in graph_service.stops_cache:
            return None

        route = await graph_service._dijkstra_with_transfers(start_stop_id, end_stop_id, optimize_for)
        return route

    async def get_stop_suggestions(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Get stop suggestions for autocomplete
        """
        db = await get_database()

        # Case-insensitive regex search
        cursor = db.stops.find(
            {"name": {"$regex": query, "$options": "i"}},
            {"stop_id": 1, "name": 1, "location": 1}
        ).limit(limit)

        suggestions = []
        async for stop in cursor:
            suggestions.append({
                "stop_id": stop["stop_id"],
                "name": stop["name"],
                "latitude": stop["location"]["coordinates"][1],
                "longitude": stop["location"]["coordinates"][0]
            })

        return suggestions


# Global instance
route_optimizer = RouteOptimizer()
