from typing import Any, Dict, Optional
from app.core.logging import logger
from app.core.redis import cache_service
from app.tools.base import BaseTool, ToolResult
from app.tools.finance.providers.base import BaseFinanceProvider
from app.tools.finance.providers.composite import ResilientFinanceProvider
from app.tools.finance.schemas import FinanceInput, FinanceOutput
from app.tools.finance.symbols import resolve_ticker_symbol


class FinanceTool(BaseTool):
    """
    Production-ready Financial Market Tool for AI Hub.
    Fetches real-time stock equity quotes, indices, and performance statistics with caching and resilience.
    """

    def __init__(self, provider: Optional[BaseFinanceProvider] = None):
        self._provider = provider or ResilientFinanceProvider()

    @property
    def name(self) -> str:
        return "get_market_quote"

    @property
    def category(self) -> str:
        return "Finance"

    @property
    def description(self) -> str:
        return (
            "Get real-time stock equity quotes, market indices, trading volume, day high/low, "
            "and percentage change for company stocks and indices (e.g. 'AAPL', 'Tesla', 'NVDA', 'SPY'). "
            "Use this tool whenever the user asks about stock prices, share value, or market quotes."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker symbol or company name (e.g. 'AAPL', 'Apple', 'TSLA', 'Tesla', 'NVDA', 'SPY').",
                },
            },
            "required": ["symbol"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        # Step 1: Input validation via Pydantic
        try:
            validated = FinanceInput(**kwargs)
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Invalid arguments for finance tool: {e}",
            )

        raw_symbol = validated.symbol.strip()
        ticker = resolve_ticker_symbol(raw_symbol)

        # Step 2: Cache check (quotes cached for 2 minutes)
        cache_key = f"finance:{ticker}"
        cached_data = await cache_service.get_json(cache_key)
        if cached_data:
            logger.info(f"FinanceTool: Cache HIT for '{ticker}'")
            return ToolResult(
                success=True,
                data=cached_data,
                cached=True,
                provider=self._provider.provider_name,
            )

        # Step 3: Fetch from provider
        try:
            output: FinanceOutput = await self._provider.fetch_quote(symbol=ticker)
            data_dict = output.model_dump()

            # Cache successful response
            await cache_service.set_json(cache_key, data_dict, ttl_seconds=120)

            logger.info(
                f"FinanceTool: Fetched live quote for '{ticker}' via {self._provider.provider_name}"
            )
            return ToolResult(
                success=True,
                data=data_dict,
                cached=False,
                provider=self._provider.provider_name,
            )
        except ValueError as ve:
            return ToolResult(
                success=False,
                error=str(ve),
                provider=self._provider.provider_name,
            )
        except Exception as e:
            logger.error(f"FinanceTool fetch failed for '{ticker}': {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Financial market service temporarily unavailable: {str(e)}",
                provider=self._provider.provider_name,
            )
