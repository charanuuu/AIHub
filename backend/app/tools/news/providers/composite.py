from typing import List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.tools.news.providers.base import BaseNewsProvider
from app.tools.news.providers.google_news import GoogleNewsProvider
from app.tools.news.providers.hacker_news import HackerNewsProvider
from app.tools.news.providers.news_api import NewsApiOrgProvider
from app.tools.news.schemas import NewsOutput


class ResilientNewsProvider(BaseNewsProvider):
    """
    Composite news provider with automatic failover between Google News, Hacker News, and NewsAPI.
    """

    def __init__(self, providers: Optional[List[BaseNewsProvider]] = None):
        if providers:
            self._providers = providers
        else:
            self._providers = [GoogleNewsProvider(), HackerNewsProvider()]
            if settings.NEWS_API_KEY and settings.NEWS_API_KEY.strip():
                self._providers.append(NewsApiOrgProvider())

        self._last_active_provider = self._providers[0].provider_name

    @property
    def provider_name(self) -> str:
        return self._last_active_provider

    async def fetch_news(
        self, query: Optional[str] = None, category: str = "general", limit: int = 5
    ) -> NewsOutput:
        errors = []
        for provider in self._providers:
            try:
                result = await provider.fetch_news(query=query, category=category, limit=limit)
                self._last_active_provider = provider.provider_name
                return result
            except ValueError:
                # If truly no articles, don't silently swallow
                raise
            except Exception as e:
                logger.warning(
                    f"News provider '{provider.provider_name}' failed for query='{query}': {e}"
                )
                errors.append(f"{provider.provider_name}: {e}")

        raise RuntimeError(f"All news providers failed: {'; '.join(errors)}")
