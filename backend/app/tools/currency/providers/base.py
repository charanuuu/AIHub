import abc
from app.tools.currency.schemas import CurrencyOutput


class BaseCurrencyProvider(abc.ABC):
    """
    Abstract interface for Currency Exchange data providers.
    Supports Frankfurter, ExchangeRate-API, Fixer, etc.
    """

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        pass

    @abc.abstractmethod
    async def convert(
        self, from_currency: str, to_currency: str, amount: float = 1.0
    ) -> CurrencyOutput:
        """
        Fetch live exchange rate and calculate converted amount.
        """
        pass
