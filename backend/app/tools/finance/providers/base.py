import abc
from app.tools.finance.schemas import FinanceOutput


class BaseFinanceProvider(abc.ABC):
    """
    Abstract interface for financial market data providers.
    Supports Yahoo Finance, Finnhub, Alpha Vantage, etc.
    """

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        pass

    @abc.abstractmethod
    async def fetch_quote(self, symbol: str) -> FinanceOutput:
        """
        Fetch real-time stock quote and daily statistics.
        """
        pass
