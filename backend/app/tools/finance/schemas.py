from typing import Optional
from pydantic import BaseModel, Field


class FinanceInput(BaseModel):
    symbol: str = Field(..., description="Stock or index ticker symbol (e.g. 'AAPL', 'MSFT', 'TSLA', 'NVDA', 'SPY')")


class FinanceOutput(BaseModel):
    symbol: str = Field(..., description="Ticker symbol")
    name: Optional[str] = Field(None, description="Company or asset name")
    price: float = Field(..., description="Current market price")
    change: Optional[float] = Field(None, description="Absolute price change today")
    change_percent: Optional[float] = Field(None, description="Percentage price change today")
    day_high: Optional[float] = Field(None, description="Highest price today")
    day_low: Optional[float] = Field(None, description="Lowest price today")
    volume: Optional[int] = Field(None, description="Trading volume")
    previous_close: Optional[float] = Field(None, description="Previous session closing price")
    currency: str = Field("USD", description="Quoted currency")
    exchange: Optional[str] = Field(None, description="Listing exchange name")
    provider: str = Field(..., description="Market data provider")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
