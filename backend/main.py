from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import logging
import asyncio
from contextlib import asynccontextmanager

from routers import github, architecture
from redis_db.connection import redis_manager
from services.data_ingestion_service import data_ingestion_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    logger.info("Starting ArchiMind Backend...")
    await redis_manager.connect()
    if redis_manager.is_connected():
        logger.info("✅ Redis connection established")
    else:
        logger.warning("⚠️ Redis connection failed - some features may not work")
    
    print("INFO:     🚀 Triggering background data ingestion from AWS Architecture Center...")
    asyncio.create_task(data_ingestion_service.ingest_website("https://aws.amazon.com/architecture/"))
    
    yield
    
    logger.info("Shutting down ArchiMind Backend...")
    await redis_manager.disconnect()
    logger.info("👋 Redis connection closed")

app = FastAPI(
    title="ArchiMind Backend",
    description="AI-powered AWS architecture design platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation Error", "detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred"}
    )

# Include routers
# app.include_router(github.router, prefix="/api/github", tags=["GitHub"])
app.include_router(architecture.router, prefix="/api/architecture", tags=["Architecture"])
# app.include_router(aws.router, prefix="/api/aws", tags=["AWS"])
# app.include_router(optimization.router, prefix="/api/optimization", tags=["Optimization"])
# app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
# app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])

@app.get("/")
async def root():
    return {"message": "ArchiMind Backend API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    redis_status = await redis_manager.ping() if redis_manager.is_connected() else False
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "redis_connected": redis_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))