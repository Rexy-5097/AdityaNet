from fastapi import APIRouter, Response, status
from app.core.redis import redis_service
from app.db.session import check_db_health
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": HealthResponse,
            "description": "TimescaleDB or Redis connection is offline",
        }
    },
)
async def health_check(response: Response) -> HealthResponse:
    """Check connections to backing services (TimescaleDB and Redis)."""
    db_ok = await check_db_health()
    redis_ok = await redis_service.check_health()

    db_status = "connected" if db_ok else "disconnected"
    redis_status = "connected" if redis_ok else "disconnected"

    is_healthy = db_ok and redis_ok
    status_str = "ok" if is_healthy else "error"

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=status_str,
        project="SuryaNet",
        database=db_status,
        redis=redis_status,
    )
