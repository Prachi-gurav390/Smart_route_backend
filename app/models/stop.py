from typing import List, Optional, Dict, Any, Annotated
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId


def validate_object_id(v):
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class Location(BaseModel):
    type: str = "Point"
    coordinates: List[float] = Field(..., description="[longitude, latitude]")


class Connection(BaseModel):
    to_stop_id: str
    route_id: str
    time: int = Field(..., description="Travel time in minutes")
    cost: float = Field(..., description="Cost in currency units")
    sequence: int = Field(..., description="Order in route")


class Stop(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    stop_id: str = Field(..., unique=True)
    name: str
    location: Location
    connections: List[Connection] = []

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class StopCreate(BaseModel):
    stop_id: str
    name: str
    latitude: float
    longitude: float


class StopResponse(BaseModel):
    stop_id: str
    name: str
    latitude: float
    longitude: float
    connections: List[Connection] = []
