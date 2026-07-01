import logging
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    def __init__(self) -> None:
        self.client: aioredis.Redis | None = None

    def connect(self) -> None:
        """Initialize connection pool and client."""
        logger.info("Initializing Redis connection client...")
        self.client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def close(self) -> None:
        """Close connection client."""
        if self.client:
            logger.info("Closing Redis connection...")
            await self.client.aclose()
            self.client = None

    async def check_health(self) -> bool:
        """Ping Redis server to verify connection."""
        if not self.client:
            return False
        try:
            # ping returns True if successful
            return await self.client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


redis_service = RedisService()
