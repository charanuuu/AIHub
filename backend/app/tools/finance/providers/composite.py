from typing import List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.tools.finance.providers.base import BaseFinanceProvider
from app.tools.finance.providers.yahoo import YahooFinanceProvider
from app.tools.finance.providers.finnhub import FinnhubFinanceProvider
from app.tools.finance.schemas import FinanceOutput


class ResilientFinanceProvider(BaseFinanceProvider):
    """
    Composite finance provider with failover across Yahoo Finance and Finnhub.
    """

    def __init__(self, providers: Optional[List[BaseFinanceProvider]] = None):
        if providers:
            self._providers = providers
        else:
            self._providers = [YahooFinanceProvider()]
            if settings.FINNHUB_API_KEY and settings.FINNHUB_API_KEY.strip():
                self._providers.append(FinnhubFinanceProvider())

        self._last_active_provider = self._providers[0].provider_name

    @property
    def provider_name(self) -> str:
        return self._last_active_provider

    async def fetch_quote(self, symbol: str) -> FinanceOutput:
        errors = []
        for provider in self._providers:
            try:
                result = await provider.fetch_quote(symbol)
                self._last_active_provider = provider.provider_name
                return result
            except ValueError:
                # If ticker is invalid, don't swallow
                raise
            except Exception as e:
                logger.warning(
                    f"Finance provider '{provider.provider_name}' failed for '{symbol}': {e}"
                )
                errors.append(f"{provider.provider_name}: {e}")

        raise RuntimeError(f"All finance providers failed: {'; '.join(errors)}")
