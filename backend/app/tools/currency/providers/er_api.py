from datetime import datetime, timezone
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.tools.currency.providers.base import BaseCurrencyProvider
from app.tools.currency.schemas import CurrencyOutput


class ExchangeRateApiProvider(BaseCurrencyProvider):
    """
    ExchangeRate-API provider.
    Supports free open-access endpoint (open.er-api.com) and authenticated v6 endpoint if API key configured.
    Covers 160+ world currencies.
    """

    OPEN_URL = "https://open.er-api.com/v6/latest"

    @property
    def provider_name(self) -> str:
        return "exchangerate_api"

    async def convert(
        self, from_currency: str, to_currency: str, amount: float = 1.0
    ) -> CurrencyOutput:
        from_curr = from_currency.upper().strip()
        to_curr = to_currency.upper().strip()

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

        # If custom API key is present in environment, use authenticated endpoint
        if settings.EXCHANGERATE_API_KEY and settings.EXCHANGERATE_API_KEY.strip():
            url = f"https://v6.exchangerate-api.com/v6/{settings.EXCHANGERATE_API_KEY.strip()}/pair/{from_curr}/{to_curr}/{amount}"
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                if data.get("result") == "error":
                    raise ValueError(data.get("error-type", "Unknown ExchangeRate-API error"))
                rate = float(data.get("conversion_rate", 1.0))
                converted_amount = float(data.get("conversion_result", amount * rate))
                return CurrencyOutput(
                    from_currency=from_curr,
                    to_currency=to_curr,
                    amount=amount,
                    converted_amount=round(converted_amount, 4),
                    exchange_rate=round(rate, 6),
                    date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    provider=self.provider_name,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

        # Otherwise use keyless open access endpoint
        url = f"{self.OPEN_URL}/{from_curr}"
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

            if data.get("result") != "success":
                raise ValueError(f"ExchangeRate-API returned status: {data.get('result')}")

            rates = data.get("rates", {})
            if to_curr not in rates:
                raise ValueError(f"Target currency '{to_curr}' not supported or found in rates.")

            rate = float(rates[to_curr])
            converted_amount = amount * rate
            date_str = data.get("time_last_update_utc", "")[:16] if data.get("time_last_update_utc") else datetime.now(timezone.utc).strftime("%Y-%m-%d")

            return CurrencyOutput(
                from_currency=from_curr,
                to_currency=to_curr,
                amount=amount,
                converted_amount=round(converted_amount, 4),
                exchange_rate=round(rate, 6),
                date=date_str,
                provider=self.provider_name,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
