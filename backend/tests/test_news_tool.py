from typing import Optional
import pytest
from app.agent.router import AgentRouter
from app.tools.news.schemas import NewsArticle, NewsInput, NewsOutput
from app.tools.news.providers.base import BaseNewsProvider
from app.tools.news.tool import NewsTool


class MockNewsProvider(BaseNewsProvider):
    @property
    def provider_name(self) -> str:
        return "mock_news"

    async def fetch_news(
        self, query: Optional[str] = None, category: str = "general", limit: int = 5
    ) -> NewsOutput:
        articles = [
            NewsArticle(
                title=f"Sample Breakthrough Article {i} on {query or category}",
                source="Global Tech Wire",
                url=f"https://example.com/news/{i}",
                published_at="Fri, 25 Sep 2026 14:00:00 GMT",
                summary="Researchers unveil unprecedented system enhancements.",
            )
            for i in range(1, limit + 1)
        ]

        return NewsOutput(
            topic=query or category.capitalize(),
            category=category,
            total_results=len(articles),
            articles=articles,
            provider=self.provider_name,
            timestamp="2026-09-25T14:00:00Z",
        )


@pytest.mark.asyncio
async def test_news_tool_openai_schema():
    tool = NewsTool()
    schema = tool.to_openai_tool()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "get_latest_news"
    params = schema["function"]["parameters"]
    assert "query" in params["properties"]
    assert "category" in params["properties"]
    assert "limit" in params["properties"]


@pytest.mark.asyncio
async def test_news_tool_mock_execution():
    mock_provider = MockNewsProvider()
    tool = NewsTool(provider=mock_provider)

    result = await tool.execute_with_resilience(category="technology", limit=3)
    assert result.success is True
    assert result.data is not None
    assert len(result.data["articles"]) == 3
    assert result.data["category"] == "technology"
    assert result.provider == "mock_news"
    assert result.cached is False


@pytest.mark.asyncio
async def test_news_tool_caching():
    mock_provider = MockNewsProvider()
    tool = NewsTool(provider=mock_provider)

    # First call - cache miss
    result1 = await tool.execute(category="science", limit=2)
    assert result1.success is True
    assert result1.cached is False

    # Second call - cache hit
    result2 = await tool.execute(category="science", limit=2)
    assert result2.success is True
    assert result2.cached is True
    assert len(result2.data["articles"]) == 2


@pytest.mark.asyncio
async def test_news_tool_validation():
    tool = NewsTool()
    # Invalid limit (> 10)
    result = await tool.execute(limit=50)
    assert result.success is False
    assert "Invalid arguments" in result.error


@pytest.mark.asyncio
async def test_agent_router_news_fallback():
    router = AgentRouter()
    answer, tools = await router.run("What is the latest technology news today?")
    assert len(tools) == 1
    assert tools[0].tool_name == "get_latest_news"
    assert "Headlines" in answer
