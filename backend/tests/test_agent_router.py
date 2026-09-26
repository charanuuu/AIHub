import pytest
from app.agent.router import AgentRouter
from app.tools.registry import tool_registry
from app.tools.weather.tool import WeatherTool
from tests.test_weather_tool import MockWeatherProvider


@pytest.mark.asyncio
async def test_agent_fallback_routing_weather():
    # Use mock provider for reproducible test
    mock_tool = WeatherTool(provider=MockWeatherProvider())
    tool_registry.register(mock_tool)

    router = AgentRouter()
    answer, executed_tools = await router.run("What is the weather in Bangalore tomorrow?")

    assert len(executed_tools) == 1
    tool_call = executed_tools[0]
    assert tool_call.tool_name == "get_weather"
    assert tool_call.arguments["city"] == "Bangalore"
    assert tool_call.success is True
    assert "Bangalore" in answer
    assert "Temperature:" in answer


@pytest.mark.asyncio
async def test_agent_fallback_routing_greetings():
    router = AgentRouter()
    answer, executed_tools = await router.run("Hello there!")

    assert len(executed_tools) == 0
    assert "AI Hub" in answer


@pytest.mark.asyncio
async def test_agent_extract_city():
    router = AgentRouter()
    assert router._extract_city_from_query("What is the weather in Paris?") == "Paris"
    assert router._extract_city_from_query("Give me weather for Tokyo tomorrow") == "Tokyo"
    assert router._extract_city_from_query("London") == "London"
