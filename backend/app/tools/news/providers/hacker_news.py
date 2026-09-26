import asyncio
from datetime import datetime, timezone
from typing import List, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.tools.news.providers.base import BaseNewsProvider
from app.tools.news.schemas import NewsArticle, NewsOutput


class HackerNewsProvider(BaseNewsProvider):
    """
    Hacker News API provider for technology and software engineering news.
    Keyless, free, powered by official Firebase API.
    """

    TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
    ITEM_URL = "https://hacker-news.firebaseio.com/v0/item"

    @property
    def provider_name(self) -> str:
        return "hacker_news"

    async def fetch_news(
        self, query: Optional[str] = None, category: str = "general", limit: int = 5
    ) -> NewsOutput:
        timeout = httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS)

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(self.TOP_STORIES_URL)
            resp.raise_for_status()
            story_ids: List[int] = resp.json()[:limit * 2]

            # Fetch top story items concurrently
            tasks = [client.get(f"{self.ITEM_URL}/{sid}.json") for sid in story_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        articles: List[NewsArticle] = []
        q_lower = query.lower().strip() if query else None

        for res in results:
            if isinstance(res, httpx.Response) and res.status_code == 200:
                item = res.json()
                if not item:
                    continue
                title = item.get("title", "")
                url = item.get("url")

                # If query specified, filter by keyword
                if q_lower and q_lower not in title.lower():
                    continue

                ts = item.get("time")
                pub_time_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT") if ts else None

                articles.append(
                    NewsArticle(
                        title=title,
                        source="Hacker News",
                        url=url,
                        published_at=pub_time_str,
                        summary=f"Score: {item.get('score', 0)} | By: {item.get('by', 'anonymous')}",
                    )
                )

                if len(articles) >= limit:
                    break

        # If filtered by query and none matched, take top without filter
        if not articles and results:
            for res in results[:limit]:
                if isinstance(res, httpx.Response) and res.status_code == 200:
                    item = res.json()
                    if item:
                        articles.append(
                            NewsArticle(
                                title=item.get("title", ""),
                                source="Hacker News",
                                url=item.get("url"),
                                published_at=None,
                                summary=f"Score: {item.get('score', 0)}",
                            )
                        )

        if not articles:
            raise ValueError(f"No news stories retrieved from Hacker News.")

        return NewsOutput(
            topic=query or "Technology News",
            category=category or "technology",
            total_results=len(articles),
            articles=articles,
            provider=self.provider_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
