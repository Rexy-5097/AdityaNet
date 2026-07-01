from fastapi import APIRouter
from app.api.v1.endpoints import health, solar, flares, system, inference

api_router = APIRouter()

# Include endpoint sub-routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(solar.router, prefix="/solar", tags=["solar"])
api_router.include_router(flares.router, prefix="/flares", tags=["flares"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(inference.router, prefix="/predict", tags=["predict"])

