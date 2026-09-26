import abc
from typing import Optional
from app.tools.news.schemas import NewsOutput


class BaseNewsProvider(abc.ABC):
    """
    Abstract interface for news data providers.
    Supports Google News RSS, Hacker News, NewsAPI, etc.
    """

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        pass

    @abc.abstractmethod
    async def fetch_news(
        self, query: Optional[str] = None, category: str = "general", limit: int = 5
    ) -> NewsOutput:
        """
        Fetch verified news headlines and summaries.
        """
        pass
