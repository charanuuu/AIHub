from datetime import datetime, timezone
from typing import Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.tools.currency.providers.base import BaseCurrencyProvider
from app.tools.currency.schemas import CurrencyOutput


class FrankfurterCurrencyProvider(BaseCurrencyProvider):
    """
    Frankfurter API currency provider (tracks European Central Bank reference rates).
    100% free, keyless, open-source.
    """

    BASE_URLS = [
        "https://api.frankfurter.dev/v1/latest",
        "https://api.frankfurter.app/latest",
    ]

    @property
    def provider_name(self) -> str:
        return "frankfurter"

    async def convert(
        self, from_currency: str, to_currency: str, amount: float = 1.0
    ) -> CurrencyOutput:
        from_curr = from_currency.upper().strip()
        to_curr = to_currency.upper().strip()

        # Handle identity conversion directly
        if from_curr == to_curr:
            now_str = datetime.now(timezone.utc).isoformat()
            return CurrencyOutput(
                from_currency=from_curr,
                to_currency=to_curr,
                amount=amount,
                converted_amount=round(amount, 4),
                exchange_rate=1.0,
                date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                provider=self.provider_name,
                timestamp=now_str,
            )

        timeout = httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS)
        last_exception: Optional[Exception] = None

        for url in self.BASE_URLS:
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.get(
                        url,
                        params={"amount": amount, "from": from_curr, "to": to_curr},
                    )
                    if resp.status_code == 404:
                        raise ValueError(f"Currency pair {from_curr}->{to_curr} not supported by Frankfurter.")
                    resp.raise_for_status()
                    data = resp.json()

                    rates = data.get("rates", {})
                    if to_curr not in rates:
                        raise ValueError(f"Target currency '{to_curr}' not found in exchange rates response.")

                    converted_amount = float(rates[to_curr])
                    rate = converted_amount / amount if amount > 0 else 0.0

                    return CurrencyOutput(
                        from_currency=from_curr,
                        to_currency=to_curr,
                        amount=amount,
                        converted_amount=round(converted_amount, 4),
                        exchange_rate=round(rate, 6),
                        date=data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
                        provider=self.provider_name,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
            except ValueError:
                raise
            except Exception as e:
                last_exception = e
                logger.warning(f"Frankfurter endpoint '{url}' failed: {e}. Trying fallback if available.")

        raise last_exception or RuntimeError("All Frankfurter endpoints failed.")
