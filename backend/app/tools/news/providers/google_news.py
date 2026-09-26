from datetime import datetime, timezone
from typing import List, Optional
import urllib.parse
import xml.etree.ElementTree as ET
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.tools.news.providers.base import BaseNewsProvider
from app.tools.news.schemas import NewsArticle, NewsOutput

TOPIC_MAP = {
    "technology": "TECHNOLOGY",
    "tech": "TECHNOLOGY",
    "business": "BUSINESS",
    "finance": "BUSINESS",
    "science": "SCIENCE",
    "health": "HEALTH",
    "entertainment": "ENTERTAINMENT",
    "sports": "SPORTS",
}


class GoogleNewsProvider(BaseNewsProvider):
    """
    Google News RSS provider.
    Delivers real-time world headlines and topic-specific search results.
    Keyless, fast, and globally updated.
    """

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }

    @property
    def provider_name(self) -> str:
        return "google_news"

    async def fetch_news(
        self, query: Optional[str] = None, category: str = "general", limit: int = 5
    ) -> NewsOutput:
        cat_lower = (category or "general").lower().strip()

        if query and query.strip():
            topic_label = query.strip()
            encoded_query = urllib.parse.quote_plus(topic_label)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        elif cat_lower in TOPIC_MAP:
            topic_label = cat_lower.capitalize()
            url = f"https://news.google.com/rss/headlines/section/topic/{TOPIC_MAP[cat_lower]}?hl=en-US&gl=US&ceid=US:en"
        else:
            topic_label = "Top Stories"
            url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"

        timeout = httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS)
        async with httpx.AsyncClient(timeout=timeout, headers=self.HEADERS) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            xml_text = resp.text

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as pe:
            raise RuntimeError(f"Failed to parse news RSS response: {pe}")

        items = root.findall(".//item")
        articles: List[NewsArticle] = []

        for item in items[:limit]:
            raw_title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "").strip()

            source_elem = item.find("source")
            source_name = source_elem.text.strip() if source_elem is not None and source_elem.text else ""

            # If title ends with " - Source Name", clean it up
            if not source_name and " - " in raw_title:
                parts = raw_title.rsplit(" - ", 1)
                clean_title = parts[0].strip()
                source_name = parts[1].strip()
            else:
                clean_title = raw_title

            articles.append(
                NewsArticle(
                    title=clean_title,
                    source=source_name or "News Network",
                    url=link or None,
                    published_at=pub_date or None,
                    summary=None,
                )
            )

        if not articles:
            raise ValueError(f"No news articles found for query='{query}' or category='{category}'.")

        return NewsOutput(
            topic=topic_label,
            category=cat_lower,
            total_results=len(articles),
            articles=articles,
            provider=self.provider_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
