from fastapi import APIRouter
from app.api.v1.endpoints import chat, health, tools

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(tools.router, prefix="/tools", tags=["Tools"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
