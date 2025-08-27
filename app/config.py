import os
from typing import Optional


class Settings:
    # Database
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "smartroute")

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "SmartRoute API"
    VERSION: str = "1.0.0"

    # Algorithm parameters
    TRANSFER_PENALTY_TIME: int = 5  # minutes
    TRANSFER_PENALTY_COST: float = 0.5  # currency units
    WALKING_SPEED_KMH: float = 5.0  # km/h for connecting nearby stops
    MAX_WALKING_DISTANCE_KM: float = 0.5  # max walking distance to connect stops
    MAX_SEARCH_RADIUS_KM: float = 50.0  # max distance from any stop to accept coordinates
    
    # Transit mode specific parameters
    BUS_BOARDING_TIME: int = 2  # minutes to board bus
    METRO_BOARDING_TIME: int = 1  # minutes to board metro
    TRANSFER_WALKING_TIME: int = 3  # minutes to walk between platforms
    TRANSFER_WAITING_TIME: int = 5  # average waiting time for next vehicle

    # Cache
    CACHE_TTL_SECONDS: int = 300  # 5 minutes

    class Config:
        case_sensitive = True


settings = Settings()
