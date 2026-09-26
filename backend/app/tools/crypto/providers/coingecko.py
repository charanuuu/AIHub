from datetime import datetime, timezone
from typing import Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.tools.crypto.providers.base import BaseCryptoProvider
from app.tools.crypto.schemas import CryptoOutput
from app.tools.crypto.symbols import resolve_crypto_symbol


class CoinGeckoProvider(BaseCryptoProvider):
    """
    CoinGecko API provider for real-time cryptocurrency metrics.
    Supports prices, market cap, and 24h change percentages in multiple fiat currencies.
    """

    BASE_URL = "https://api.coingecko.com/api/v3/simple/price"

    @property
    def provider_name(self) -> str:
        return "coingecko"

    async def fetch_crypto(
        self, coin_id: str, vs_currency: str = "usd"
    ) -> CryptoOutput:
        cg_id, _, display_name, display_ticker = resolve_crypto_symbol(coin_id)
        vs_curr = vs_currency.lower().strip()

        headers = {"accept": "application/json"}
        if settings.COINGECKO_API_KEY and settings.COINGECKO_API_KEY.strip():
            headers["x-cg-demo-api-key"] = settings.COINGECKO_API_KEY.strip()

        params = {
            "ids": cg_id,
            "vs_currencies": vs_curr,
            "include_24hr_change": "true",
            "include_market_cap": "true",
        }

        timeout = httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(self.BASE_URL, params=params, headers=headers)
            if resp.status_code == 429:
                raise RuntimeError("CoinGecko rate limit reached (HTTP 429).")
            resp.raise_for_status()
            data = resp.json()

        if cg_id not in data:
            raise ValueError(f"Cryptocurrency '{coin_id}' not found or has no price data.")

        coin_data = data[cg_id]
        if vs_curr not in coin_data:
            raise ValueError(f"Currency '{vs_curr}' not supported for coin '{coin_id}'.")

        price = float(coin_data[vs_curr])
        change_24h = coin_data.get(f"{vs_curr}_24h_change")
        if change_24h is not None:
            change_24h = round(float(change_24h), 2)
        mcap = coin_data.get(f"{vs_curr}_market_cap")
        if mcap is not None:
            mcap = round(float(mcap), 2)

        return CryptoOutput(
            coin_id=cg_id,
            name=display_name,
            symbol=display_ticker,
            vs_currency=vs_curr.upper(),
            current_price=price,
            price_change_24h_percent=change_24h,
            market_cap=mcap,
            provider=self.provider_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
