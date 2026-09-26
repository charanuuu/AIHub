from datetime import datetime, timezone
from typing import Optional
import httpx
from app.core.config import settings
from app.tools.weather.providers.base import BaseWeatherProvider
from app.tools.weather.schemas import (
    CurrentConditions,
    WeatherOutput,
)


class OpenWeatherMapProvider(BaseWeatherProvider):
    """
    OpenWeatherMap provider implementation.
    Requires OPENWEATHER_API_KEY in environment variables.
    """

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENWEATHER_API_KEY

    @property
    def provider_name(self) -> str:
        return "open_weather_map"

    async def fetch_weather(
        self, city: str, days: int = 1, unit: str = "celsius"
    ) -> WeatherOutput:
        if not self.api_key:
            raise ValueError(
                "OPENWEATHER_API_KEY is not configured in environment variables."
            )

        units_param = "imperial" if unit.lower() == "fahrenheit" else "metric"
        timeout = httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS)

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                self.BASE_URL,
                params={
                    "q": city,
                    "appid": self.api_key,
                    "units": units_param,
                },
            )
            resp.raise_for_status()
            data = resp.json()

            main = data.get("main", {})
            weather_desc = data.get("weather", [{}])[0].get("description", "Unknown")
            wind = data.get("wind", {})
            coord = data.get("coord", {})

            current = CurrentConditions(
                temperature=float(main.get("temp", 0.0)),
                feels_like=float(main.get("feels_like", 0.0)),
                humidity=int(main.get("humidity", 0)),
                condition=weather_desc.title(),
                wind_speed=float(wind.get("speed", 0.0)) * 3.6,  # m/s to km/h
                precipitation=0.0,
                weather_code=0,
            )

            return WeatherOutput(
                city=data.get("name", city),
                country=data.get("sys", {}).get("country", ""),
                latitude=float(coord.get("lat", 0.0)),
                longitude=float(coord.get("lon", 0.0)),
                unit=unit,
                current=current,
                forecast=[],
                provider=self.provider_name,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
