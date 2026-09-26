from typing import Any, Dict, Optional
from app.core.logging import logger
from app.core.redis import cache_service
from app.tools.base import BaseTool, ToolResult
from app.tools.currency.providers.base import BaseCurrencyProvider
from app.tools.currency.providers.composite import ResilientCurrencyProvider
from app.tools.currency.schemas import CurrencyInput, CurrencyOutput


class CurrencyExchangeTool(BaseTool):
    """
    Production-ready Currency Exchange & Conversion Tool for AI Hub.
    Fetches real-time foreign exchange rates and executes conversions with caching and failover.
    """

    def __init__(self, provider: Optional[BaseCurrencyProvider] = None):
        self._provider = provider or ResilientCurrencyProvider()

    @property
    def name(self) -> str:
        return "convert_currency"

    @property
    def category(self) -> str:
        return "Currency"

    @property
    def description(self) -> str:
        return (
            "Convert an amount between two currencies using real-time foreign exchange rates. "
            "Use this tool whenever the user asks to convert money (e.g. 'Convert 50,000 INR to USD') "
            "or asks for current exchange rates between currencies."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "The numeric amount to convert. Defaults to 1.0.",
                    "minimum": 0.01,
                    "default": 1.0,
                },
                "from_currency": {
                    "type": "string",
                    "description": "The source 3-letter currency code, e.g. 'USD', 'INR', 'EUR', 'GBP', 'JPY'.",
                },
                "to_currency": {
                    "type": "string",
                    "description": "The target 3-letter currency code, e.g. 'USD', 'INR', 'EUR', 'GBP', 'JPY'.",
                },
            },
            "required": ["from_currency", "to_currency"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        # Step 1: Input validation via Pydantic
        try:
            validated = CurrencyInput(**kwargs)
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Invalid arguments for currency tool: {e}",
            )

        from_curr = validated.from_currency.upper().strip()
        to_curr = validated.to_currency.upper().strip()
        amount = validated.amount

        # Step 2: Cache check (rates cached for 15 minutes)
        cache_key = f"currency:{from_curr}:{to_curr}:{round(amount, 2)}"
        cached_data = await cache_service.get_json(cache_key)
        if cached_data:
            logger.info(f"CurrencyExchangeTool: Cache HIT for {amount} {from_curr}->{to_curr}")
            return ToolResult(
                success=True,
                data=cached_data,
                cached=True,
                provider=self._provider.provider_name,
            )

        # Step 3: Fetch from provider
        try:
            output: CurrencyOutput = await self._provider.convert(
                from_currency=from_curr,
                to_currency=to_curr,
                amount=amount,
            )
            data_dict = output.model_dump()

            # Cache successful conversion
            await cache_service.set_json(cache_key, data_dict, ttl_seconds=900)

            logger.info(
                f"CurrencyExchangeTool: Converted {amount} {from_curr} to {output.converted_amount} {to_curr} via {self._provider.provider_name}"
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
            logger.error(f"CurrencyExchangeTool conversion failed for {from_curr}->{to_curr}: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Currency exchange service unavailable: {str(e)}",
                provider=self._provider.provider_name,
            )
