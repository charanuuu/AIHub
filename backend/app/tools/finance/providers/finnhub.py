from datetime import datetime, timezone
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.tools.finance.providers.base import BaseFinanceProvider
from app.tools.finance.schemas import FinanceOutput
from app.tools.finance.symbols import resolve_ticker_symbol


class FinnhubFinanceProvider(BaseFinanceProvider):
    """
    Finnhub Stock API provider.
    Activated when FINNHUB_API_KEY is configured in the environment.
    """

    BASE_URL = "https://finnhub.io/api/v1/quote"

    @property
    def provider_name(self) -> str:
        return "finnhub"

    async def fetch_quote(self, symbol: str) -> FinanceOutput:
        if not settings.FINNHUB_API_KEY or not settings.FINNHUB_API_KEY.strip():
            raise RuntimeError("FINNHUB_API_KEY not configured in environment.")

        ticker = resolve_ticker_symbol(symbol)
        params = {"symbol": ticker, "token": settings.FINNHUB_API_KEY.strip()}
        timeout = httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS)

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(self.BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        current_price = data.get("c", 0.0)
        if current_price == 0.0:
            raise ValueError(f"Ticker '{ticker}' not found or zero price on Finnhub.")

        change = data.get("d")
        change_pct = data.get("dp")
        high = data.get("h")
        low = data.get("l")
        prev = data.get("pc")

        return FinanceOutput(
            symbol=ticker,
            name=ticker,
            price=float(current_price),
            change=round(float(change), 2) if change is not None else None,
            change_percent=round(float(change_pct), 2) if change_pct is not None else None,
            day_high=float(high) if high is not None else None,
            day_low=float(low) if low is not None else None,
            previous_close=float(prev) if prev is not None else None,
            currency="USD",
            provider=self.provider_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
