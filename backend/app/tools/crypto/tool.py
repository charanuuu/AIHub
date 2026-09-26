from typing import Any, Dict, Optional
from app.core.logging import logger
from app.core.redis import cache_service
from app.tools.base import BaseTool, ToolResult
from app.tools.crypto.providers.base import BaseCryptoProvider
from app.tools.crypto.providers.composite import ResilientCryptoProvider
from app.tools.crypto.schemas import CryptoInput, CryptoOutput


class CryptoTool(BaseTool):
    """
    Production-ready Cryptocurrency Tool for AI Hub.
    Fetches real-time crypto prices, 24h market performance, and market cap with failover and caching.
    """

    def __init__(self, provider: Optional[BaseCryptoProvider] = None):
        self._provider = provider or ResilientCryptoProvider()

    @property
    def name(self) -> str:
        return "get_crypto_summary"

    @property
    def category(self) -> str:
        return "Cryptocurrency"

    @property
    def description(self) -> str:
        return (
            "Fetch real-time cryptocurrency market summary, prices, 24-hour price change percentage, "
            "and market cap for tokens like Bitcoin (BTC), Ethereum (ETH), Solana (SOL), and others. "
            "Use this tool whenever the user asks about cryptocurrency prices, Bitcoin, or crypto trends."
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "coin_id": {
                    "type": "string",
                    "description": "The cryptocurrency name or ticker, e.g. 'bitcoin', 'BTC', 'ethereum', 'ETH', 'solana', 'SOL'.",
                },
                "vs_currency": {
                    "type": "string",
                    "description": "Comparison fiat currency (default 'usd', or 'eur', 'inr', 'gbp').",
                    "default": "usd",
                },
            },
            "required": ["coin_id"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        # Step 1: Input validation via Pydantic
        try:
            validated = CryptoInput(**kwargs)
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Invalid arguments for crypto tool: {e}",
            )

        coin_id = validated.coin_id.strip()
        vs_curr = (validated.vs_currency or "usd").lower().strip()

        # Step 2: Cache check (crypto cached for 2 minutes)
        cache_key = f"crypto:{coin_id.lower()}:{vs_curr}"
        cached_data = await cache_service.get_json(cache_key)
        if cached_data:
            logger.info(f"CryptoTool: Cache HIT for '{coin_id}' ({vs_curr})")
            return ToolResult(
                success=True,
                data=cached_data,
                cached=True,
                provider=self._provider.provider_name,
            )

        # Step 3: Fetch from provider
        try:
            output: CryptoOutput = await self._provider.fetch_crypto(
                coin_id=coin_id,
                vs_currency=vs_curr,
            )
            data_dict = output.model_dump()

            # Cache successful result
            await cache_service.set_json(cache_key, data_dict, ttl_seconds=120)

            logger.info(
                f"CryptoTool: Fetched live crypto for '{coin_id}' via {self._provider.provider_name}"
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
            logger.error(f"CryptoTool fetch failed for '{coin_id}': {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Cryptocurrency service temporarily unavailable: {str(e)}",
                provider=self._provider.provider_name,
            )
