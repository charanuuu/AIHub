from typing import Any, Dict, Optional
from app.core.logging import logger
from app.core.redis import cache_service
from app.tools.base import BaseTool, ToolResult
from app.tools.news.providers.base import BaseNewsProvider
from app.tools.news.providers.composite import ResilientNewsProvider
from app.tools.news.schemas import NewsInput, NewsOutput


class NewsTool(BaseTool):
    """
    Production-ready News Tool for AI Hub.
    Fetches real-time news headlines, sources, and links with caching and failover.
    """

    def __init__(self, provider: Optional[BaseNewsProvider] = None):
        self._provider = provider or ResilientNewsProvider()

    @property
    def name(self) -> str:
        return "get_latest_news"

    @property
    def category(self) -> str:
        return "News"

    @property
    def description(self) -> str:
        return (
            "Fetch the latest verified news headlines, articles, and sources across categories "
            "(general, technology, business, science, health, entertainment, sports) or specific search topics. "
            "Use this tool whenever the user asks for current news, headlines, or updates on an event or topic."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Specific search topic, keyword, or company (e.g. 'artificial intelligence', 'NASA', 'Apple'). Optional.",
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "general",
                        "technology",
                        "business",
                        "science",
                        "health",
                        "entertainment",
                        "sports",
                    ],
                    "description": "News category to fetch if no specific search query is given. Defaults to 'general'.",
                    "default": "general",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of news articles to retrieve (1 to 10). Defaults to 5.",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                },
            },
        }

    async def execute(self, **kwargs) -> ToolResult:
        # Step 1: Input validation via Pydantic
        try:
            validated = NewsInput(**kwargs)
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Invalid arguments for news tool: {e}",
            )

        query = validated.query.strip() if validated.query else None
        category = (validated.category or "general").lower().strip()
        limit = validated.limit or 5

        # Step 2: Cache check (news cached for 10 minutes)
        cache_key = f"news:{category}:{query or 'none'}:{limit}"
        cached_data = await cache_service.get_json(cache_key)
        if cached_data:
            logger.info(f"NewsTool: Cache HIT for '{query or category}'")
            return ToolResult(
                success=True,
                data=cached_data,
                cached=True,
                provider=self._provider.provider_name,
            )

        # Step 3: Fetch from provider
        try:
            output: NewsOutput = await self._provider.fetch_news(
                query=query,
                category=category,
                limit=limit,
            )
            data_dict = output.model_dump()

            # Cache successful result
            await cache_service.set_json(cache_key, data_dict, ttl_seconds=600)

            logger.info(
                f"NewsTool: Fetched {len(output.articles)} articles for '{query or category}' via {self._provider.provider_name}"
            )
            return ToolResult(
                success=True,
                data=data_dict,
                cached=False,
                provider=self._provider.provider_name,
            )
        except ValueError as ve:
            return ToolResult(
                success=False,
                error=str(ve),
                provider=self._provider.provider_name,
            )
        except Exception as e:
            logger.error(f"NewsTool fetch failed for '{query or category}': {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"News service temporarily unavailable: {str(e)}",
                provider=self._provider.provider_name,
            )
