from typing import List, Optional
from app.core.logging import logger
from app.tools.currency.providers.base import BaseCurrencyProvider
from app.tools.currency.providers.frankfurter import FrankfurterCurrencyProvider
from app.tools.currency.providers.er_api import ExchangeRateApiProvider
from app.tools.currency.schemas import CurrencyOutput


class ResilientCurrencyProvider(BaseCurrencyProvider):
    """
    Composite provider with automatic failover across Frankfurter and ExchangeRate-API.
    """

    def __init__(self, providers: Optional[List[BaseCurrencyProvider]] = None):
        self._providers = providers or [
            FrankfurterCurrencyProvider(),
            ExchangeRateApiProvider(),
        ]
        self._last_active_provider = self._providers[0].provider_name

    @property
    def provider_name(self) -> str:
        return self._last_active_provider

    async def convert(
        self, from_currency: str, to_currency: str, amount: float = 1.0
    ) -> CurrencyOutput:
        errors = []
        for provider in self._providers:
            try:
                result = await provider.convert(from_currency, to_currency, amount)
                self._last_active_provider = provider.provider_name
                return result
            except Exception as e:
                logger.warning(
                    f"Currency provider '{provider.provider_name}' failed for {from_currency}->{to_currency}: {e}"
                )
                errors.append(f"{provider.provider_name}: {e}")

        raise RuntimeError(f"All currency providers failed: {'; '.join(errors)}")
