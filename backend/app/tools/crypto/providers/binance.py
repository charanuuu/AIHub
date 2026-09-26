from datetime import datetime, timezone
import httpx
from app.core.config import settings
from app.tools.crypto.providers.base import BaseCryptoProvider
from app.tools.crypto.schemas import CryptoOutput
from app.tools.crypto.symbols import resolve_crypto_symbol


class BinanceCryptoProvider(BaseCryptoProvider):
    """
    Binance API provider for ultra-fast, high-availability crypto price quotes.
    Free, keyless, high throughput.
    """

    BASE_URL = "https://api.binance.com/api/v3/ticker/24hr"

    @property
    def provider_name(self) -> str:
        return "binance"

    async def fetch_crypto(
        self, coin_id: str, vs_currency: str = "usd"
    ) -> CryptoOutput:
        cg_id, binance_symbol, display_name, display_ticker = resolve_crypto_symbol(coin_id)

        timeout = httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(self.BASE_URL, params={"symbol": binance_symbol})
            if resp.status_code == 400:
                raise ValueError(f"Ticker symbol '{binance_symbol}' not available on Binance.")
            resp.raise_for_status()
            data = resp.json()

        last_price = float(data.get("lastPrice", 0.0))
        change_pct = float(data.get("priceChangePercent", 0.0))
        high_24h = float(data.get("highPrice", 0.0))
        low_24h = float(data.get("lowPrice", 0.0))

        return CryptoOutput(
            coin_id=cg_id,
            name=display_name,
            symbol=display_ticker,
            vs_currency="USD",
            current_price=last_price,
            price_change_24h_percent=round(change_pct, 2),
            high_24h=round(high_24h, 2),
            low_24h=round(low_24h, 2),
            provider=self.provider_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
