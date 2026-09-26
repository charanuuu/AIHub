from typing import Optional
from pydantic import BaseModel, Field


class CryptoInput(BaseModel):
    coin_id: str = Field(..., description="Cryptocurrency name or ticker, e.g. 'bitcoin', 'BTC', 'ethereum', 'ETH', 'solana', 'SOL'")
    vs_currency: Optional[str] = Field("usd", description="Target comparison currency, e.g. 'usd', 'eur', 'inr', 'gbp'")


class CryptoOutput(BaseModel):
    coin_id: str = Field(..., description="Coin identifier")
    name: str = Field(..., description="Full cryptocurrency name")
    symbol: str = Field(..., description="Cryptocurrency ticker symbol (e.g. BTC)")
    vs_currency: str = Field(..., description="Comparison currency")
    current_price: float = Field(..., description="Current price")
    price_change_24h_percent: Optional[float] = Field(None, description="24-hour price change percentage")
    market_cap: Optional[float] = Field(None, description="Total market capitalization")
    high_24h: Optional[float] = Field(None, description="24-hour high price")
    low_24h: Optional[float] = Field(None, description="24-hour low price")
    provider: str = Field(..., description="Data provider name")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
