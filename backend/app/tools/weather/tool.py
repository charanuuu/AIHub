from typing import Any, Dict, Optional
from app.core.logging import logger
from app.core.redis import cache_service
from app.tools.base import BaseTool, ToolResult
from app.tools.weather.providers.base import BaseWeatherProvider
from app.tools.weather.providers.open_meteo import OpenMeteoWeatherProvider
from app.tools.weather.schemas import WeatherInput, WeatherOutput


class WeatherTool(BaseTool):
    """
    Production-ready Weather Tool for AI Hub.
    Fetches real-time weather and forecasts with caching and provider fallback.
    """

    def __init__(self, provider: Optional[BaseWeatherProvider] = None):
        self._provider = provider or OpenMeteoWeatherProvider()

    @property
    def name(self) -> str:
        return "get_weather"

    @property
    def category(self) -> str:
        return "Weather"

    @property
    def description(self) -> str:
        return (
            "Get current weather conditions and 1-7 day forecast for any city or location worldwide. "
            "Use this tool whenever the user asks about temperature, rain, clouds, forecast, or weather."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city or location name, e.g. 'Bangalore', 'New York', 'Paris', 'Tokyo'.",
                },
                "days": {
                    "type": "integer",
                    "description": "Number of forecast days (1 to 7). Defaults to 1 for current weather.",
                    "minimum": 1,
                    "maximum": 7,
                    "default": 1,
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit to return.",
                    "default": "celsius",
                },
            },
            "required": ["city"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        # Step 1: Validate input through Pydantic schema
        try:
            validated = WeatherInput(**kwargs)
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Invalid arguments for weather tool: {e}",
            )

        city = validated.city.strip()
        days = validated.days or 1
        unit = (validated.unit or "celsius").lower()

        # Step 2: Check cache
        cache_key = f"weather:{city.lower()}:{unit}:{days}"
        cached_data = await cache_service.get_json(cache_key)
        if cached_data:
            logger.info(f"WeatherTool: Cache HIT for '{city}'")
            return ToolResult(
                success=True,
                data=cached_data,
                cached=True,
                provider=self._provider.provider_name,
            )

        # Step 3: Fetch from provider
        try:
            weather_output: WeatherOutput = await self._provider.fetch_weather(
                city=city, days=days, unit=unit
            )
            data_dict = weather_output.model_dump()

            # Step 4: Cache response for 10 minutes (600s)
            await cache_service.set_json(cache_key, data_dict, ttl_seconds=600)

            logger.info(
                f"WeatherTool: Fetched live weather for '{city}' via {self._provider.provider_name}"
            )
            return ToolResult(
                success=True,
                data=data_dict,
                cached=False,
                provider=self._provider.provider_name,
            )
        except ValueError as ve:
            # Geocoding / city not found
            return ToolResult(
                success=False,
                error=str(ve),
                provider=self._provider.provider_name,
            )
        except Exception as e:
            logger.error(f"WeatherTool fetch failed for '{city}': {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Weather service temporarily unavailable: {str(e)}",
                provider=self._provider.provider_name,
            )
