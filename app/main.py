from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection, database
from app.api.routes import router
from app.services.graph_service import graph_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Public Transport Route Optimizer API"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server  
        "https://*.vercel.app",   # Vercel deployments
        "https://*.netlify.app",  # Netlify deployments
        # Add your frontend domain here when deployed
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Initialize application"""
    logger.info("Starting SmartRoute API...")
    try:
        await connect_to_mongo()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database during startup: {e}")
        logger.info("API will start without database connection")
    
    # Load graph data in background, don't block startup
    import asyncio
    asyncio.create_task(load_graph_data_background())


async def load_graph_data_background():
    """Load graph data in background without blocking startup"""
    try:
        logger.info("Loading graph data in background...")
        # Ensure database is connected before loading graph data
        if database.database is None:
            await connect_to_mongo()
        await graph_service.load_graph_data()
        logger.info("Graph data loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load graph data: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down SmartRoute API...")
    await close_mongo_connection()
    logger.info("SmartRoute API shut down")


@app.get("/")
async def root():
    """Simple root endpoint that doesn't depend on database"""
    return {
        "message": "Welcome to SmartRoute API",
        "version": settings.VERSION,
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
