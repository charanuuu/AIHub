from typing import Optional
from pydantic import BaseModel, Field


class CurrencyInput(BaseModel):
    amount: float = Field(default=1.0, gt=0, description="Amount to convert (must be greater than 0)")
    from_currency: str = Field(..., description="Base currency 3-letter code, e.g. 'USD', 'INR', 'EUR', 'GBP'")
    to_currency: str = Field(..., description="Target currency 3-letter code, e.g. 'USD', 'INR', 'EUR', 'JPY'")


class CurrencyOutput(BaseModel):
    from_currency: str = Field(..., description="Base currency code")
    to_currency: str = Field(..., description="Target currency code")
    amount: float = Field(..., description="Original input amount")
    converted_amount: float = Field(..., description="Calculated converted amount")
    exchange_rate: float = Field(..., description="Exchange rate (1 from_currency = rate to_currency)")
    date: str = Field(..., description="Date of the exchange rate")
    provider: str = Field(..., description="Name of the data provider")
    timestamp: str = Field(..., description="ISO 8601 timestamp of response")
