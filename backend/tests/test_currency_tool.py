import pytest
from app.agent.router import AgentRouter
from app.tools.currency.schemas import CurrencyInput, CurrencyOutput
from app.tools.currency.providers.base import BaseCurrencyProvider
from app.tools.currency.tool import CurrencyExchangeTool


class MockCurrencyProvider(BaseCurrencyProvider):
    @property
    def provider_name(self) -> str:
        return "mock_currency"

    async def convert(
        self, from_currency: str, to_currency: str, amount: float = 1.0
    ) -> CurrencyOutput:
        from_curr = from_currency.upper()
        to_curr = to_currency.upper()
        if from_curr == "INVALID":
            raise ValueError(f"Currency code '{from_curr}' is invalid.")

        # Fixed mock exchange rates for testing
        rates = {
            ("INR", "USD"): 0.012,
            ("USD", "INR"): 83.33,
            ("EUR", "USD"): 1.08,
            ("USD", "EUR"): 0.92,
        }
        rate = rates.get((from_curr, to_curr), 1.25)
        converted = round(amount * rate, 4)

        return CurrencyOutput(
            from_currency=from_curr,
            to_currency=to_curr,
            amount=amount,
            converted_amount=converted,
            exchange_rate=rate,
            date="2026-09-25",
            provider=self.provider_name,
            timestamp="2026-09-25T12:00:00Z",
        )


@pytest.mark.asyncio
async def test_currency_tool_openai_schema():
    tool = CurrencyExchangeTool()
    schema = tool.to_openai_tool()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "convert_currency"
    params = schema["function"]["parameters"]
    assert "from_currency" in params["properties"]
    assert "to_currency" in params["properties"]
    assert "amount" in params["properties"]
    assert "from_currency" in params["required"]
    assert "to_currency" in params["required"]


@pytest.mark.asyncio
async def test_currency_tool_mock_execution():
    mock_provider = MockCurrencyProvider()
    tool = CurrencyExchangeTool(provider=mock_provider)

    result = await tool.execute_with_resilience(
        amount=50000.0, from_currency="INR", to_currency="USD"
    )
    assert result.success is True
    assert result.data is not None
    assert result.data["from_currency"] == "INR"
    assert result.data["to_currency"] == "USD"
    assert result.data["amount"] == 50000.0
    assert result.data["converted_amount"] == 600.0
    assert result.data["exchange_rate"] == 0.012
    assert result.provider == "mock_currency"
    assert result.cached is False


@pytest.mark.asyncio
async def test_currency_tool_caching():
    mock_provider = MockCurrencyProvider()
    tool = CurrencyExchangeTool(provider=mock_provider)

    # First call - cache miss
    result1 = await tool.execute(amount=100.0, from_currency="EUR", to_currency="USD")
    assert result1.success is True
    assert result1.cached is False

    # Second call - cache hit
    result2 = await tool.execute(amount=100.0, from_currency="EUR", to_currency="USD")
    assert result2.success is True
    assert result2.cached is True
    assert result2.data["converted_amount"] == 108.0


@pytest.mark.asyncio
async def test_currency_tool_invalid_currency():
    mock_provider = MockCurrencyProvider()
    tool = CurrencyExchangeTool(provider=mock_provider)

    result = await tool.execute(amount=50.0, from_currency="INVALID", to_currency="USD")
    assert result.success is False
    assert "invalid" in result.error.lower()


@pytest.mark.asyncio
async def test_currency_tool_validation():
    tool = CurrencyExchangeTool()
    # Amount <= 0 is invalid
    result = await tool.execute(amount=-5.0, from_currency="USD", to_currency="EUR")
    assert result.success is False
    assert "Invalid arguments" in result.error


@pytest.mark.asyncio
async def test_agent_router_currency_fallback():
    router = AgentRouter()
    answer, tools = await router.run("Convert 50,000 INR to USD.")
    assert len(tools) == 1
    assert tools[0].tool_name == "convert_currency"
    assert "Currency Conversion" in answer
    assert "INR" in answer
    assert "USD" in answer
