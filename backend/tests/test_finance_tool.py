import pytest
from app.agent.router import AgentRouter
from app.tools.finance.schemas import FinanceInput, FinanceOutput
from app.tools.finance.providers.base import BaseFinanceProvider
from app.tools.finance.tool import FinanceTool


class MockFinanceProvider(BaseFinanceProvider):
    @property
    def provider_name(self) -> str:
        return "mock_finance"

    async def fetch_quote(self, symbol: str) -> FinanceOutput:
        ticker = symbol.upper().strip()
        if ticker == "NONEXISTENTTICKER999":
            raise ValueError(f"Ticker '{symbol}' not found.")

        quotes = {
            "AAPL": ("Apple Inc.", 340.50, 3.50, 1.04, 342.0, 336.0, 45000000, 337.0, "NASDAQ"),
            "TSLA": ("Tesla, Inc.", 375.00, -5.20, -1.37, 382.0, 370.0, 60000000, 380.2, "NASDAQ"),
            "MSFT": ("Microsoft Corporation", 520.00, 8.00, 1.56, 524.0, 515.0, 22000000, 512.0, "NASDAQ"),
        }

        q = quotes.get(ticker, (ticker, 150.0, 1.0, 0.67, 152.0, 148.0, 1000000, 149.0, "NYSE"))

        return FinanceOutput(
            symbol=ticker,
            name=q[0],
            price=q[1],
            change=q[2],
            change_percent=q[3],
            day_high=q[4],
            day_low=q[5],
            volume=q[6],
            previous_close=q[7],
            currency="USD",
            exchange=q[8],
            provider=self.provider_name,
            timestamp="2026-09-25T14:30:00Z",
        )


@pytest.mark.asyncio
async def test_finance_tool_openai_schema():
    tool = FinanceTool()
    schema = tool.to_openai_tool()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "get_market_quote"
    params = schema["function"]["parameters"]
    assert "symbol" in params["properties"]
    assert "symbol" in params["required"]


@pytest.mark.asyncio
async def test_finance_tool_mock_execution():
    mock_provider = MockFinanceProvider()
    tool = FinanceTool(provider=mock_provider)

    result = await tool.execute_with_resilience(symbol="AAPL")
    assert result.success is True
    assert result.data is not None
    assert result.data["symbol"] == "AAPL"
    assert result.data["name"] == "Apple Inc."
    assert result.data["price"] == 340.50
    assert result.data["change_percent"] == 1.04
    assert result.provider == "mock_finance"
    assert result.cached is False


@pytest.mark.asyncio
async def test_finance_tool_caching():
    mock_provider = MockFinanceProvider()
    tool = FinanceTool(provider=mock_provider)

    # First call - cache miss
    result1 = await tool.execute(symbol="TSLA")
    assert result1.success is True
    assert result1.cached is False

    # Second call - cache hit
    result2 = await tool.execute(symbol="TSLA")
    assert result2.success is True
    assert result2.cached is True
    assert result2.data["price"] == 375.00


@pytest.mark.asyncio
async def test_finance_tool_invalid_ticker():
    mock_provider = MockFinanceProvider()
    tool = FinanceTool(provider=mock_provider)

    result = await tool.execute(symbol="NONEXISTENTTICKER999")
    assert result.success is False
    assert "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_finance_tool_validation():
    tool = FinanceTool()
    # Missing required 'symbol'
    result = await tool.execute()
    assert result.success is False
    assert "Invalid arguments" in result.error


@pytest.mark.asyncio
async def test_agent_router_finance_fallback():
    router = AgentRouter()
    answer, tools = await router.run("What is the Apple stock price today?")
    assert len(tools) == 1
    assert tools[0].tool_name == "get_market_quote"
    assert "AAPL" in answer
    assert "Market Quote" in answer
    assert "Current Price" in answer
