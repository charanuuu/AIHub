from datetime import datetime, timezone
from typing import Optional
import httpx
from app.core.config import settings
from app.tools.news.providers.base import BaseNewsProvider
from app.tools.news.schemas import NewsArticle, NewsOutput


class NewsApiOrgProvider(BaseNewsProvider):
    """
    NewsAPI.org provider.
    Activated when NEWS_API_KEY is configured in the environment.
    """

    BASE_URL = "https://newsapi.org/v2/top-headlines"

    @property
    def provider_name(self) -> str:
        return "news_api"

    async def fetch_news(
        self, query: Optional[str] = None, category: str = "general", limit: int = 5
    ) -> NewsOutput:
        if not settings.NEWS_API_KEY or not settings.NEWS_API_KEY.strip():
            raise RuntimeError("NEWS_API_KEY not configured in environment.")

        params = {
            "apiKey": settings.NEWS_API_KEY.strip(),
            "pageSize": limit,
        }
        if query:
            params["q"] = query
        else:
            params["category"] = category
            params["country"] = "us"

        timeout = httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(self.BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        if data.get("status") != "ok":
            raise ValueError(f"NewsAPI error: {data.get('message', 'Unknown error')}")

        raw_articles = data.get("articles", [])
        articles = [
            NewsArticle(
                title=a.get("title", ""),
                source=a.get("source", {}).get("name", "News"),
                url=a.get("url"),
                published_at=a.get("publishedAt"),
                summary=a.get("description"),
            )
            for a in raw_articles[:limit]
        ]

        return NewsOutput(
            topic=query or category.capitalize(),
            category=category,
            total_results=len(articles),
            articles=articles,
            provider=self.provider_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
