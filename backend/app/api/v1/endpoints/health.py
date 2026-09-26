from fastapi import APIRouter
from sqlalchemy import text
from app.core.config import settings
from app.core.database import async_session_factory
from app.core.redis import cache_service
from app.models.schemas import HealthStatus
from app.tools.registry import tool_registry

router = APIRouter()


@router.get("/health", response_model=HealthStatus)
async def health_check():
    # Database check
    db_status = {"status": "healthy"}
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = {"status": "degraded", "error": str(e)}

    # Cache check
    cache_status = await cache_service.health_check()

    return HealthStatus(
        status="healthy" if db_status["status"] == "healthy" else "degraded",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        database=db_status,
        cache=cache_status,
        tools_count=len(tool_registry._tools),
    )
