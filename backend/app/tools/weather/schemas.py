from typing import List, Optional
from pydantic import BaseModel, Field


class WeatherInput(BaseModel):
    city: str = Field(..., description="The city name, e.g. 'Bangalore', 'London', 'Tokyo'")
    days: Optional[int] = Field(
        1, ge=1, le=7, description="Number of forecast days (1 to 7)"
    )
    unit: Optional[str] = Field(
        "celsius", description="Temperature unit: 'celsius' or 'fahrenheit'"
    )


class CurrentConditions(BaseModel):
    temperature: float = Field(..., description="Current temperature in requested unit")
    feels_like: float = Field(..., description="Apparent / feels-like temperature")
    humidity: int = Field(..., description="Relative humidity percentage (0-100)")
    condition: str = Field(..., description="Human-readable condition (e.g. Sunny, Rain)")
    wind_speed: float = Field(..., description="Wind speed in km/h")
    precipitation: float = Field(..., description="Current precipitation in mm")
    weather_code: int = Field(..., description="WMO weather interpretation code")


class DailyForecast(BaseModel):
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    max_temperature: float = Field(..., description="Maximum temperature")
    min_temperature: float = Field(..., description="Minimum temperature")
    condition: str = Field(..., description="Condition description")
    precipitation_sum: float = Field(..., description="Precipitation sum in mm")
    weather_code: int = Field(..., description="WMO weather interpretation code")


class WeatherOutput(BaseModel):
    city: str
    country: str
    latitude: float
    longitude: float
    unit: str
    current: CurrentConditions
    forecast: List[DailyForecast] = Field(default_factory=list)
    provider: str
    timestamp: str
