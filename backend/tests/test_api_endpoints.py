import pytest
from httpx import AsyncClient
from app.tools.registry import tool_registry
from app.tools.weather.tool import WeatherTool
from tests.test_weather_tool import MockWeatherProvider


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    resp = await async_client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["app"] == "AI Hub"
    assert data["status"] == "online"


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["tools_count"] >= 1


@pytest.mark.asyncio
async def test_list_tools_endpoint(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/tools")
    assert resp.status_code == 200
    tools = resp.json()
    assert len(tools) >= 1
    tool_names = [t["name"] for t in tools]
    assert "get_weather" in tool_names


@pytest.mark.asyncio
async def test_direct_weather_tool_endpoint(async_client: AsyncClient):
    mock_tool = WeatherTool(provider=MockWeatherProvider())
    tool_registry.register(mock_tool)

    resp = await async_client.post(
        "/api/v1/tools/weather",
        json={"city": "Bangalore", "days": 1, "unit": "celsius"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["city"] == "Bangalore"


@pytest.mark.asyncio
async def test_chat_endpoint_and_history(async_client: AsyncClient):
    mock_tool = WeatherTool(provider=MockWeatherProvider())
    tool_registry.register(mock_tool)

    # 1. Send chat message asking for weather
    chat_resp = await async_client.post(
        "/api/v1/chat",
        json={"message": "What is the weather in Bangalore tomorrow?"},
    )
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    conv_id = data["conversation_id"]
    assert conv_id is not None
    assert len(data["tool_calls"]) == 1
    assert data["tool_calls"][0]["tool_name"] == "get_weather"
    assert "Bangalore" in data["message"]

    # 2. List conversations
    conv_list_resp = await async_client.get("/api/v1/chat/conversations")
    assert conv_list_resp.status_code == 200
    conversations = conv_list_resp.json()
    assert any(c["id"] == conv_id for c in conversations)

    # 3. Get messages for the conversation
    msgs_resp = await async_client.get(f"/api/v1/chat/conversations/{conv_id}/messages")
    assert msgs_resp.status_code == 200
    messages = msgs_resp.json()
    assert len(messages) >= 2  # user + assistant

    # 4. Delete the conversation
    del_resp = await async_client.delete(f"/api/v1/chat/conversations/{conv_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "success"
