import pytest
from app.tools.weather.tool import WeatherTool
from app.tools.weather.schemas import WeatherInput, WeatherOutput, CurrentConditions, DailyForecast
from app.tools.weather.providers.base import BaseWeatherProvider
from app.core.redis import cache_service


class MockWeatherProvider(BaseWeatherProvider):
    @property
    def provider_name(self) -> str:
        return "mock_weather"

    async def fetch_weather(
        self, city: str, days: int = 1, unit: str = "celsius"
    ) -> WeatherOutput:
        if city.lower() == "nonexistentcity12345":
            raise ValueError(f"City '{city}' was not found. Please verify spelling.")

        return WeatherOutput(
            city=city,
            country="India",
            latitude=12.97,
            longitude=77.59,
            unit=unit,
            current=CurrentConditions(
                temperature=24.5,
                feels_like=25.0,
                humidity=65,
                condition="Partly cloudy",
                wind_speed=12.0,
                precipitation=0.0,
                weather_code=2,
            ),
            forecast=[
                DailyForecast(
                    date="2026-09-26",
                    max_temperature=28.0,
                    min_temperature=19.0,
                    condition="Partly cloudy",
                    precipitation_sum=0.2,
                    weather_code=2,
                )
            ],
            provider=self.provider_name,
            timestamp="2026-09-25T08:00:00Z",
        )


@pytest.mark.asyncio
async def test_weather_tool_openai_schema():
    tool = WeatherTool()
    schema = tool.to_openai_tool()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "get_weather"
    assert "city" in schema["function"]["parameters"]["properties"]
    assert "city" in schema["function"]["parameters"]["required"]


@pytest.mark.asyncio
async def test_weather_tool_successful_execution():
    mock_provider = MockWeatherProvider()
    tool = WeatherTool(provider=mock_provider)

    result = await tool.execute_with_resilience(city="Bangalore", days=1, unit="celsius")
    assert result.success is True
    assert result.data is not None
    assert result.data["city"] == "Bangalore"
    assert result.data["current"]["temperature"] == 24.5
    assert result.provider == "mock_weather"
    assert result.cached is False


@pytest.mark.asyncio
async def test_weather_tool_caching():
    mock_provider = MockWeatherProvider()
    tool = WeatherTool(provider=mock_provider)

    # First call - cache miss
    result1 = await tool.execute(city="Chennai", days=1, unit="celsius")
    assert result1.success is True
    assert result1.cached is False

    # Second call - should hit cache
    result2 = await tool.execute(city="Chennai", days=1, unit="celsius")
    assert result2.success is True
    assert result2.cached is True


@pytest.mark.asyncio
async def test_weather_tool_invalid_city():
    mock_provider = MockWeatherProvider()
    tool = WeatherTool(provider=mock_provider)

    result = await tool.execute(city="nonexistentcity12345")
    assert result.success is False
    assert "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_weather_tool_input_validation():
    tool = WeatherTool()
    # Invalid days (< 1 or > 7)
    result = await tool.execute(city="London", days=10)
    assert result.success is False
    assert "Invalid arguments" in result.error
