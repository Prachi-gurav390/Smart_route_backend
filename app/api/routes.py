from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
import logging

from app.services.route_optimizer import route_optimizer
from app.models.route import OptimizedRoute

logger = logging.getLogger(__name__)
router = APIRouter()


class RouteRequest(BaseModel):
    start: Dict[str, float] = Field(...,
                                    description="Start coordinates {lat, lon}")
    end: Dict[str, float] = Field(...,
                                  description="End coordinates {lat, lon}")
    optimize_for: str = Field(
        default="time", description="time, cost, or transfers")


class StopRouteRequest(BaseModel):
    start_stop_id: str
    end_stop_id: str
    optimize_for: str = Field(
        default="time", description="time, cost, or transfers")


@router.post("/route", response_model=OptimizedRoute)
async def find_route(request: RouteRequest):
    """
    Find optimal route between two coordinates
    """
    try:
        # Validate optimization criteria
        if request.optimize_for not in ["time", "cost", "transfers"]:
            raise HTTPException(
                status_code=400, detail="optimize_for must be 'time', 'cost', or 'transfers'")

        # Validate coordinates
        start_lat = request.start.get("lat")
        start_lon = request.start.get("lon")
        end_lat = request.end.get("lat")
        end_lon = request.end.get("lon")

        if not all([start_lat, start_lon, end_lat, end_lon]):
            raise HTTPException(
                status_code=400, detail="Missing coordinates. Required: start.lat, start.lon, end.lat, end.lon")

        # Validate coordinate ranges
        if not (-90 <= start_lat <= 90) or not (-180 <= start_lon <= 180):
            raise HTTPException(
                status_code=400, detail="Invalid start coordinates. Latitude must be between -90 and 90, longitude between -180 and 180")

        if not (-90 <= end_lat <= 90) or not (-180 <= end_lon <= 180):
            raise HTTPException(
                status_code=400, detail="Invalid end coordinates. Latitude must be between -90 and 90, longitude between -180 and 180")

        # Find route
        route = await route_optimizer.find_route(
            start_lat, start_lon, end_lat, end_lon, request.optimize_for
        )

        if not route:
            raise HTTPException(
                status_code=404, detail="No route found. Check if coordinates are within service area and walking distance limits.")

        return route

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding route: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error occurred while finding route")


@router.post("/route/stops", response_model=OptimizedRoute)
async def find_route_by_stops(request: StopRouteRequest):
    """
    Find optimal route between two specific stops
    """
    try:
        if request.optimize_for not in ["time", "cost", "transfers"]:
            raise HTTPException(
                status_code=400, detail="optimize_for must be 'time', 'cost', or 'transfers'")

        # Validate stop IDs exist
        from app.services.graph_service import graph_service

        if not graph_service.stops_cache:
            await graph_service.load_graph_data()

        if request.start_stop_id not in graph_service.stops_cache:
            raise HTTPException(
                status_code=400, detail=f"Start stop '{request.start_stop_id}' not found")

        if request.end_stop_id not in graph_service.stops_cache:
            raise HTTPException(
                status_code=400, detail=f"End stop '{request.end_stop_id}' not found")

        route = await route_optimizer.find_route_by_stops(
            request.start_stop_id, request.end_stop_id, request.optimize_for
        )

        if not route:
            raise HTTPException(
                status_code=404, detail="No route found between the specified stops")

        return route

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding route by stops: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error occurred while finding route between stops")


@router.get("/stops/search")
async def search_stops(
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=10, le=50, description="Maximum results")
):
    """
    Search for stops by name
    """
    try:
        suggestions = await route_optimizer.get_stop_suggestions(q, limit)
        return {"suggestions": suggestions}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching stops: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error occurred while searching stops")


@router.get("/stops/nearby")
async def get_nearby_stops(
    lat: float = Query(..., description="Latitude", ge=-90, le=90),
    lon: float = Query(..., description="Longitude", ge=-180, le=180),
    limit: int = Query(default=10, le=50, description="Maximum results")
):
    """
    Get nearby stops to given coordinates
    """
    try:
        from app.services.graph_service import graph_service

        if not graph_service.stops_cache:
            await graph_service.load_graph_data()

        # Validate coordinates are within service area
        if not graph_service.validate_coordinates(lat, lon):
            raise HTTPException(
                status_code=400,
                detail="Coordinates are too far from service area. Please check if you're within the supported region."
            )

        nearby_stops_with_dist = graph_service.find_nearest_stops(
            lat, lon, limit)

        stops = []
        for stop_id, distance in nearby_stops_with_dist:
            if stop_id in graph_service.stops_cache:
                stop = graph_service.stops_cache[stop_id]
                walking_time, _ = graph_service.calculate_walking_time_from_coords(
                    lat, lon, stop_id)
                stops.append({
                    "stop_id": stop.stop_id,
                    "name": stop.name,
                    "latitude": stop.location.coordinates[1],
                    "longitude": stop.location.coordinates[0],
                    "distance_km": round(distance, 3),
                    "walking_time_minutes": walking_time if walking_time != float('inf') else None
                })

        return {"nearby_stops": stops}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding nearby stops: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error occurred while finding nearby stops")


@router.get("/graph/nodes")
async def get_graph_nodes():
    """
    Get all stops (nodes) in the transport network for graph visualization
    """
    try:
        from app.services.graph_service import graph_service
        
        if not graph_service.stops_cache:
            await graph_service.load_graph_data()
        
        nodes = []
        for stop_id, stop in graph_service.stops_cache.items():
            nodes.append({
                "id": stop.stop_id,
                "name": stop.name,
                "latitude": stop.location.coordinates[1],
                "longitude": stop.location.coordinates[0],
                "connections_count": len(stop.connections)
            })
        
        return {"nodes": nodes}
    
    except Exception as e:
        logger.error(f"Error getting graph nodes: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error occurred while fetching graph nodes")


@router.get("/graph/edges")
async def get_graph_edges():
    """
    Get all connections (edges) in the transport network for graph visualization
    """
    try:
        from app.services.graph_service import graph_service
        
        if not graph_service.stops_cache:
            await graph_service.load_graph_data()
        
        edges = []
        for stop_id, stop in graph_service.stops_cache.items():
            for connection in stop.connections:
                edge = {
                    "from": stop_id,
                    "to": connection.to_stop_id,
                    "route_id": connection.route_id,
                    "time": connection.time,
                    "cost": connection.cost,
                    "sequence": connection.sequence
                }
                
                # Get route info for edge styling
                route_info = graph_service.routes_cache.get(connection.route_id, {})
                edge["route_type"] = route_info.get("route_type", "bus")
                edge["route_name"] = route_info.get("route_long_name", f"Route {connection.route_id}")
                
                edges.append(edge)
        
        return {"edges": edges}
    
    except Exception as e:
        logger.error(f"Error getting graph edges: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error occurred while fetching graph edges")


@router.post("/graph/algorithm-steps")
async def get_algorithm_steps(request: StopRouteRequest):
    """
    Get step-by-step execution of pathfinding algorithm for visualization
    """
    try:
        from app.services.graph_service import graph_service
        
        if request.optimize_for not in ["time", "cost", "transfers"]:
            raise HTTPException(
                status_code=400, detail="optimize_for must be 'time', 'cost', or 'transfers'")
        
        if not graph_service.stops_cache:
            await graph_service.load_graph_data()
        
        if request.start_stop_id not in graph_service.stops_cache:
            raise HTTPException(
                status_code=400, detail=f"Start stop '{request.start_stop_id}' not found")
        
        if request.end_stop_id not in graph_service.stops_cache:
            raise HTTPException(
                status_code=400, detail=f"End stop '{request.end_stop_id}' not found")
        
        # Get algorithm execution steps
        steps = await graph_service.get_algorithm_execution_steps(
            request.start_stop_id, request.end_stop_id, request.optimize_for
        )
        
        return {"steps": steps}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting algorithm steps: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error occurred while getting algorithm steps")


@router.get("/graph/stats")
async def get_graph_stats():
    """
    Get network statistics for analysis display
    """
    try:
        from app.services.graph_service import graph_service
        
        if not graph_service.stops_cache:
            await graph_service.load_graph_data()
        
        total_nodes = len(graph_service.stops_cache)
        total_edges = sum(len(stop.connections) for stop in graph_service.stops_cache.values())
        
        # Calculate route type distribution
        route_types = {}
        for route_id, route_info in graph_service.routes_cache.items():
            route_type = route_info.get("route_type", "bus")
            route_types[route_type] = route_types.get(route_type, 0) + 1
        
        # Calculate connectivity stats
        max_connections = max(len(stop.connections) for stop in graph_service.stops_cache.values()) if graph_service.stops_cache else 0
        avg_connections = total_edges / total_nodes if total_nodes > 0 else 0
        
        return {
            "network_stats": {
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "total_routes": len(graph_service.routes_cache),
                "max_connections_per_stop": max_connections,
                "avg_connections_per_stop": round(avg_connections, 2),
                "route_type_distribution": route_types
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting graph stats: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error occurred while fetching graph statistics")


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "SmartRoute API"}
