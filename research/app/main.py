import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.redis import redis_service
from app.db.init_db import init_db

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Redis connection client and DB hypertables
    logger.info("Starting up SuryaNet FastAPI Application...")
    redis_service.connect()
    await init_db()

    yield

    # Shutdown: Close Redis connection client
    logger.info("Shutting down SuryaNet FastAPI Application...")
    await redis_service.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Physics-Informed Solar Flare Forecasting and Space Weather Intelligence Platform using Aditya-L1",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register routes
app.include_router(api_router, prefix=settings.API_V1_STR)
