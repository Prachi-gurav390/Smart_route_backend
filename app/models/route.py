from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.stop import PyObjectId


class Route(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    route_id: str = Field(..., unique=True)
    name: str
    stops: List[str] = Field(..., description="Ordered list of stop_ids")
    route_type: str = Field(
        default="bus", description="bus, metro, train, etc.")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class RouteCreate(BaseModel):
    route_id: str
    name: str
    stops: List[str]
    route_type: str = "bus"


class WalkingDirection(BaseModel):
    instruction: str
    distance_meters: int
    duration_seconds: int


class RouteSegment(BaseModel):
    route_id: str
    route_name: str
    route_type: str = "bus"  # bus, metro, walking
    from_stop: str
    to_stop: str
    from_stop_name: str
    to_stop_name: str
    time: int
    cost: float
    sequence_start: int
    sequence_end: int
    boarding_time: Optional[int] = 0
    transfer_time: Optional[int] = 0
    walking_directions: Optional[List[WalkingDirection]] = []


class OptimizedRoute(BaseModel):
    path: List[str]
    segments: List[RouteSegment]
    total_time: int
    total_cost: float
    transfers: int
    walking_time: int = 0
    total_distance_km: float = 0
    start_walking_time: int = 0
    end_walking_time: int = 0
    route_summary: str = ""
    alternative_routes_count: int = 0
    co2_saved_kg: Optional[float] = None
    calories_burned: Optional[int] = None
