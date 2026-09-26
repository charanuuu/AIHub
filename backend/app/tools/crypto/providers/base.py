import abc
from app.tools.crypto.schemas import CryptoOutput


class BaseCryptoProvider(abc.ABC):
    """
    Abstract interface for cryptocurrency data providers.
    Supports CoinGecko, Binance, Coinbase, etc.
    """

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        pass

    @abc.abstractmethod
    async def fetch_crypto(
        self, coin_id: str, vs_currency: str = "usd"
    ) -> CryptoOutput:
        """
        Fetch real-time cryptocurrency price, 24h change, and metrics.
        """
        pass
