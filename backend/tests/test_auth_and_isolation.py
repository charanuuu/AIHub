import pytest
from httpx import AsyncClient
from app.core.config import settings
from app.core.rate_limiter import rate_limiter
from app.core.redis import cache_service
from app.tools.registry import tool_registry
from app.tools.weather.tool import WeatherTool
from tests.test_weather_tool import MockWeatherProvider


@pytest.mark.asyncio
async def test_authentication_with_session_id(async_client: AsyncClient):
    """Verify valid X-Session-ID header is accepted and creates session-bound chat."""
    mock_tool = WeatherTool(provider=MockWeatherProvider())
    tool_registry.register(mock_tool)

    headers = {"X-Session-ID": "user-session-alice-123"}
    resp = await async_client.post(
        "/api/v1/chat",
        headers=headers,
        json={"message": "What is the weather in Bangalore tomorrow?"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["conversation_id"] is not None
    assert "Bangalore" in data["message"]


@pytest.mark.asyncio
async def test_unauthorized_when_auth_enforced(async_client: AsyncClient):
    """Verify that requests without credentials fail with 401 when auth is enforced."""
    # When X-Enforce-Auth is sent or in production mode
    resp = await async_client.post(
        "/api/v1/chat",
        headers={"X-Enforce-Auth": "true"},
        json={"message": "Hello without credentials"},
    )
    assert resp.status_code == 401
    assert "Authentication required" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_malformed_session_id(async_client: AsyncClient):
    """Verify malformed session ID is rejected with 400 Bad Request."""
    resp = await async_client.post(
        "/api/v1/chat",
        headers={"X-Session-ID": "bad id with spaces !@#$%^&*()"},
        json={"message": "Hello"},
    )
    assert resp.status_code == 400
    assert "Invalid X-Session-ID format" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_bearer_token_authentication(async_client: AsyncClient):
    """Verify Bearer token format validation."""
    mock_tool = WeatherTool(provider=MockWeatherProvider())
    tool_registry.register(mock_tool)

    # Valid Bearer token
    resp = await async_client.post(
        "/api/v1/chat",
        headers={"Authorization": "Bearer valid-token-secret-12345"},
        json={"message": "What is the weather in Bangalore tomorrow?"},
    )
    assert resp.status_code == 200

    # Malformed Bearer header
    bad_resp = await async_client.post(
        "/api/v1/chat",
        headers={"Authorization": "InvalidBearerFormat"},
        json={"message": "Hello"},
    )
    assert bad_resp.status_code == 401


@pytest.mark.asyncio
async def test_conversation_ownership_and_isolation(async_client: AsyncClient):
    """Verify complete isolation: User B cannot view or append to User A's conversation."""
    mock_tool = WeatherTool(provider=MockWeatherProvider())
    tool_registry.register(mock_tool)

    user_a_headers = {"X-Session-ID": "alice-session-001"}
    user_b_headers = {"X-Session-ID": "bob-session-002"}

    # 1. User A creates conversation A
    resp_a = await async_client.post(
        "/api/v1/chat",
        headers=user_a_headers,
        json={"message": "What is the weather in Bangalore tomorrow?"},
    )
    assert resp_a.status_code == 200
    conv_a_id = resp_a.json()["conversation_id"]

    # 2. User B lists conversations -> Conversation A must NOT be listed
    list_b_resp = await async_client.get(
        "/api/v1/chat/conversations",
        headers=user_b_headers,
    )
    assert list_b_resp.status_code == 200
    user_b_convs = list_b_resp.json()
    assert not any(c["id"] == conv_a_id for c in user_b_convs)

    # 3. User B tries to view messages of Conversation A -> 403 Forbidden
    get_msgs_resp = await async_client.get(
        f"/api/v1/chat/conversations/{conv_a_id}/messages",
        headers=user_b_headers,
    )
    assert get_msgs_resp.status_code == 403
    assert "Forbidden" in get_msgs_resp.json()["detail"]

    # 4. User B tries to post into Conversation A -> 403 Forbidden
    post_into_a_resp = await async_client.post(
        "/api/v1/chat",
        headers=user_b_headers,
        json={
            "conversation_id": conv_a_id,
            "message": "Intruding message",
        },
    )
    assert post_into_a_resp.status_code == 403
    assert "Forbidden" in post_into_a_resp.json()["detail"]

    # 5. User A can view messages of Conversation A successfully
    user_a_msgs_resp = await async_client.get(
        f"/api/v1/chat/conversations/{conv_a_id}/messages",
        headers=user_a_headers,
    )
    assert user_a_msgs_resp.status_code == 200
    assert len(user_a_msgs_resp.json()) >= 2


@pytest.mark.asyncio
async def test_deletion_ownership(async_client: AsyncClient):
    """Verify that only the owner can delete a conversation."""
    mock_tool = WeatherTool(provider=MockWeatherProvider())
    tool_registry.register(mock_tool)

    user_a_headers = {"X-Session-ID": "alice-session-002"}
    user_b_headers = {"X-Session-ID": "bob-session-003"}

    # User A creates a conversation
    resp_a = await async_client.post(
        "/api/v1/chat",
        headers=user_a_headers,
        json={"message": "What is the weather in Bangalore tomorrow?"},
    )
    conv_id = resp_a.json()["conversation_id"]

    # User B attempts to delete User A's conversation -> 403 Forbidden
    del_b_resp = await async_client.delete(
        f"/api/v1/chat/conversations/{conv_id}",
        headers=user_b_headers,
    )
    assert del_b_resp.status_code == 403
    assert "cannot delete another user's conversation" in del_b_resp.json()["detail"].lower()

    # User A deletes their own conversation -> 200 OK
    del_a_resp = await async_client.delete(
        f"/api/v1/chat/conversations/{conv_id}",
        headers=user_a_headers,
    )
    assert del_a_resp.status_code == 200
    assert del_a_resp.json()["status"] == "success"

    # Subsequent fetch confirms it is gone (404 Not Found)
    verify_resp = await async_client.get(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        headers=user_a_headers,
    )
    assert verify_resp.status_code == 404


@pytest.mark.asyncio
async def test_chat_rate_limiting(async_client: AsyncClient):
    """Verify rate limiter triggers 429 when threshold is exceeded."""
    user_headers = {"X-Session-ID": "rate-limited-user"}

    # Temporarily set a low limit for test execution
    original_limit = settings.RATE_LIMIT_CHAT_PER_MINUTE
    settings.RATE_LIMIT_CHAT_PER_MINUTE = 3

    try:
        await cache_service.clear()
        mock_tool = WeatherTool(provider=MockWeatherProvider())
        tool_registry.register(mock_tool)

        # 3 requests succeed
        for i in range(3):
            resp = await async_client.post(
                "/api/v1/chat",
                headers=user_headers,
                json={"message": "What is the weather in Bangalore tomorrow?"},
            )
            assert resp.status_code == 200

        # 4th request must be rejected with 429
        rejected_resp = await async_client.post(
            "/api/v1/chat",
            headers=user_headers,
            json={"message": "What is the weather in Bangalore tomorrow?"},
        )
        assert rejected_resp.status_code == 429
        assert "Rate limit exceeded" in rejected_resp.json()["detail"]
        assert "Retry-After" in rejected_resp.headers
    finally:
        settings.RATE_LIMIT_CHAT_PER_MINUTE = original_limit
        await cache_service.clear()


@pytest.mark.asyncio
async def test_security_headers_present(async_client: AsyncClient):
    """Verify standard production security headers are attached to responses."""
    resp = await async_client.get("/api/v1/health")
    assert resp.status_code == 200
    headers = resp.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Referrer-Policy" in headers
    assert "Content-Security-Policy" in headers
