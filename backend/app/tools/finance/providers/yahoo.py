from datetime import datetime, timezone
from typing import Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.tools.finance.providers.base import BaseFinanceProvider
from app.tools.finance.schemas import FinanceOutput
from app.tools.finance.symbols import resolve_ticker_symbol


class YahooFinanceProvider(BaseFinanceProvider):
    """
    Yahoo Finance market data provider.
    Accesses real-time stock quotes, day high/low, volume, and percentage changes.
    Keyless, robust, with query1/query2 failover.
    """

    BASE_URLS = [
        "https://query1.finance.yahoo.com/v8/finance/chart",
        "https://query2.finance.yahoo.com/v8/finance/chart",
    ]

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "*/*",
    }

    @property
    def provider_name(self) -> str:
        return "yahoo_finance"

    async def fetch_quote(self, symbol: str) -> FinanceOutput:
        ticker = resolve_ticker_symbol(symbol)
        timeout = httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS)
        last_exception: Optional[Exception] = None

        for base_url in self.BASE_URLS:
            url = f"{base_url}/{ticker}"
            params = {"interval": "1d", "range": "1d"}

            try:
                async with httpx.AsyncClient(timeout=timeout, headers=self.HEADERS) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 404:
                        raise ValueError(f"Stock symbol '{ticker}' not found.")
                    resp.raise_for_status()
                    data = resp.json()

                chart = data.get("chart", {})
                error = chart.get("error")
                if error:
                    desc = error.get("description", "Symbol not found")
                    raise ValueError(f"Yahoo Finance: {desc} for symbol '{ticker}'.")

                results = chart.get("result")
                if not results or len(results) == 0:
                    raise ValueError(f"No market data returned for symbol '{ticker}'.")

                meta = results[0].get("meta", {})
                price = meta.get("regularMarketPrice")
                if price is None:
                    raise ValueError(f"No current price available for symbol '{ticker}'.")

                price = float(price)
                prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")
                if prev_close is not None:
                    prev_close = float(prev_close)
                    change = round(price - prev_close, 2)
                    change_pct = round((change / prev_close) * 100, 2)
                else:
                    change = None
                    change_pct = meta.get("regularMarketChangePercent")
                    if change_pct is not None:
                        change_pct = round(float(change_pct), 2)

                day_high = meta.get("regularMarketDayHigh")
                day_low = meta.get("regularMarketDayLow")
                volume = meta.get("regularMarketVolume")
                currency = meta.get("currency", "USD")
                company_name = meta.get("longName") or meta.get("shortName") or ticker
                exchange = meta.get("exchangeName")

                return FinanceOutput(
                    symbol=ticker,
                    name=company_name,
                    price=price,
                    change=change,
                    change_percent=change_pct,
                    day_high=float(day_high) if day_high is not None else None,
                    day_low=float(day_low) if day_low is not None else None,
                    volume=int(volume) if volume is not None else None,
                    previous_close=prev_close,
                    currency=currency,
                    exchange=exchange,
                    provider=self.provider_name,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

            except ValueError:
                raise
            except Exception as e:
                last_exception = e
                logger.warning(f"Yahoo Finance endpoint '{url}' failed: {e}. Trying secondary endpoint.")

        raise last_exception or RuntimeError(f"All Yahoo Finance endpoints failed for ticker '{ticker}'.")
