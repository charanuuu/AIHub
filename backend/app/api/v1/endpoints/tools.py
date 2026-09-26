from typing import List
from fastapi import APIRouter, HTTPException, Request
from app.core.rate_limiter import check_tool_rate_limit
from app.models.schemas import ToolInfo
from app.tools.base import ToolResult
from app.tools.registry import tool_registry
from app.tools.weather.schemas import WeatherInput

router = APIRouter()


@router.get("", response_model=List[ToolInfo])
async def list_tools():
    """List all registered tools, their categories, schema, and operational status."""
    return tool_registry.list_tools()


@router.post("/weather", response_model=ToolResult)
async def test_weather_tool(payload: WeatherInput, request: Request):
    """Directly test the Weather tool with custom parameters and rate limiting."""
    await check_tool_rate_limit(request)
    result = await tool_registry.execute_tool(
        "get_weather",
        city=payload.city,
        days=payload.days or 1,
        unit=payload.unit or "celsius",
    )
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result
