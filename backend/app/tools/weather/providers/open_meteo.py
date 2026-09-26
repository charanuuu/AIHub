from datetime import datetime, timezone
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.tools.weather.providers.base import BaseWeatherProvider
from app.tools.weather.schemas import (
    CurrentConditions,
    DailyForecast,
    WeatherOutput,
)

# WMO Weather interpretation codes (WW)
WMO_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def decode_wmo_code(code: int) -> str:
    return WMO_CODE_MAP.get(code, "Variable conditions")


CITY_ALIASES = {
    "bangalore": "Bengaluru",
    "bombay": "Mumbai",
    "calcutta": "Kolkata",
    "madras": "Chennai",
    "peking": "Beijing",
}


class OpenMeteoWeatherProvider(BaseWeatherProvider):
    """
    Open-Meteo implementation for real-time and forecast weather data.
    Keyless, robust, and free for open-source and commercial use.
    """

    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    @property
    def provider_name(self) -> str:
        return "open_meteo"

    async def fetch_weather(
        self, city: str, days: int = 1, unit: str = "celsius"
    ) -> WeatherOutput:
        timeout = httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS)
        temp_unit = "fahrenheit" if unit.lower() == "fahrenheit" else "celsius"
        lookup_city = CITY_ALIASES.get(city.strip().lower(), city.strip())

        async with httpx.AsyncClient(timeout=timeout) as client:
            # Step 1: Geocode city name to latitude/longitude
            geo_resp = await client.get(
                self.GEOCODING_URL,
                params={"name": lookup_city, "count": 5, "language": "en", "format": "json"},
            )
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()

            results = geo_data.get("results")
            if not results:
                raise ValueError(f"City '{city}' was not found. Please verify spelling.")

            # Prioritize the most populous city match
            loc = max(results, key=lambda x: x.get("population") or 0)
            lat = loc["latitude"]
            lon = loc["longitude"]
            city_name = loc.get("name", city)
            country = loc.get("country", "")

            # Step 2: Fetch current conditions & daily forecast
            forecast_resp = await client.get(
                self.FORECAST_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": [
                        "temperature_2m",
                        "relative_humidity_2m",
                        "apparent_temperature",
                        "precipitation",
                        "weather_code",
                        "wind_speed_10m",
                    ],
                    "daily": [
                        "weather_code",
                        "temperature_2m_max",
                        "temperature_2m_min",
                        "precipitation_sum",
                    ],
                    "timezone": "auto",
                    "forecast_days": min(max(days, 1), 7),
                    "temperature_unit": temp_unit,
                    "wind_speed_unit": "kmh",
                },
            )
            forecast_resp.raise_for_status()
            data = forecast_resp.json()

            current_raw = data.get("current", {})
            current_code = int(current_raw.get("weather_code", 0))

            current = CurrentConditions(
                temperature=float(current_raw.get("temperature_2m", 0.0)),
                feels_like=float(current_raw.get("apparent_temperature", 0.0)),
                humidity=int(current_raw.get("relative_humidity_2m", 0)),
                condition=decode_wmo_code(current_code),
                wind_speed=float(current_raw.get("wind_speed_10m", 0.0)),
                precipitation=float(current_raw.get("precipitation", 0.0)),
                weather_code=current_code,
            )

            # Daily forecast parsing
            daily_raw = data.get("daily", {})
            forecast_list: list[DailyForecast] = []
            dates = daily_raw.get("time", [])
            max_temps = daily_raw.get("temperature_2m_max", [])
            min_temps = daily_raw.get("temperature_2m_min", [])
            codes = daily_raw.get("weather_code", [])
            precip_sums = daily_raw.get("precipitation_sum", [])

            for i in range(len(dates)):
                f_code = int(codes[i]) if i < len(codes) else 0
                forecast_list.append(
                    DailyForecast(
                        date=str(dates[i]),
                        max_temperature=float(max_temps[i]) if i < len(max_temps) else 0.0,
                        min_temperature=float(min_temps[i]) if i < len(min_temps) else 0.0,
                        condition=decode_wmo_code(f_code),
                        precipitation_sum=float(precip_sums[i])
                        if i < len(precip_sums)
                        else 0.0,
                        weather_code=f_code,
                    )
                )

            return WeatherOutput(
                city=city_name,
                country=country,
                latitude=lat,
                longitude=lon,
                unit=temp_unit,
                current=current,
                forecast=forecast_list,
                provider=self.provider_name,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
