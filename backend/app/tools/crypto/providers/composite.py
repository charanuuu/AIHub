from typing import List, Optional
from app.core.logging import logger
from app.tools.crypto.providers.base import BaseCryptoProvider
from app.tools.crypto.providers.coingecko import CoinGeckoProvider
from app.tools.crypto.providers.binance import BinanceCryptoProvider
from app.tools.crypto.schemas import CryptoOutput


class ResilientCryptoProvider(BaseCryptoProvider):
    """
    Composite crypto provider with automatic failover between CoinGecko and Binance.
    """

    def __init__(self, providers: Optional[List[BaseCryptoProvider]] = None):
        self._providers = providers or [
            CoinGeckoProvider(),
            BinanceCryptoProvider(),
        ]
        self._last_active_provider = self._providers[0].provider_name

    @property
    def provider_name(self) -> str:
        return self._last_active_provider

    async def fetch_crypto(
        self, coin_id: str, vs_currency: str = "usd"
    ) -> CryptoOutput:
        errors = []
        for provider in self._providers:
            try:
                result = await provider.fetch_crypto(coin_id, vs_currency)
                self._last_active_provider = provider.provider_name
                return result
            except ValueError:
                # If a coin is truly not found / invalid, don't silently swallow
                raise
            except Exception as e:
                logger.warning(
                    f"Crypto provider '{provider.provider_name}' failed for coin '{coin_id}': {e}"
                )
                errors.append(f"{provider.provider_name}: {e}")

        raise RuntimeError(f"All crypto providers failed: {'; '.join(errors)}")
