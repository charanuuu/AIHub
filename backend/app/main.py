from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.logging import logger
from app.core.redis import cache_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup hooks
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
    await init_db()
    await cache_service.initialize()
    logger.info("Application startup sequence completed successfully.")

    yield

    # Shutdown hooks
    logger.info("Initiating application shutdown...")
    await cache_service.close()
    await close_db()
    logger.info("Shutdown completed.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for AI Hub Android Application with dynamic AI tool routing.",
    lifespan=lifespan,
)

# Configure CORS
allow_credentials = False if ("*" in settings.CORS_ORIGINS) else settings.CORS_ALLOW_CREDENTIALS

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.core.security import apply_security_headers

# Security Headers Middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    return apply_security_headers(response)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again."},
    )


# Mount API Router
app.include_router(api_router, prefix=settings.API_PREFIX)

from app.api.v1.endpoints.health import health_check
app.add_api_route("/health", health_check, methods=["GET"], tags=["Health"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs_url": "/docs",
        "api_v1": f"{settings.API_PREFIX}/health",
    }
