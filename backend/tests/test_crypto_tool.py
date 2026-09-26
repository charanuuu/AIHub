import pytest
from app.agent.router import AgentRouter
from app.tools.crypto.schemas import CryptoInput, CryptoOutput
from app.tools.crypto.providers.base import BaseCryptoProvider
from app.tools.crypto.tool import CryptoTool


class MockCryptoProvider(BaseCryptoProvider):
    @property
    def provider_name(self) -> str:
        return "mock_crypto"

    async def fetch_crypto(
        self, coin_id: str, vs_currency: str = "usd"
    ) -> CryptoOutput:
        coin_lower = coin_id.lower().strip()
        if coin_lower == "nonexistentcoin999":
            raise ValueError(f"Cryptocurrency '{coin_id}' not found.")

        prices = {
            "bitcoin": (83500.0, -1.25, 1650000000000.0, "Bitcoin", "BTC"),
            "btc": (83500.0, -1.25, 1650000000000.0, "Bitcoin", "BTC"),
            "ethereum": (2700.0, 2.50, 325000000000.0, "Ethereum", "ETH"),
            "eth": (2700.0, 2.50, 325000000000.0, "Ethereum", "ETH"),
            "solana": (120.0, 4.10, 70000000000.0, "Solana", "SOL"),
        }

        price_info = prices.get(coin_lower, (10.0, 0.5, 100000000.0, coin_id.capitalize(), coin_id.upper()))
        return CryptoOutput(
            coin_id=coin_lower,
            name=price_info[3],
            symbol=price_info[4],
            vs_currency=vs_currency.upper(),
            current_price=price_info[0],
            price_change_24h_percent=price_info[1],
            market_cap=price_info[2],
            high_24h=price_info[0] * 1.02,
            low_24h=price_info[0] * 0.98,
            provider=self.provider_name,
            timestamp="2026-09-25T12:00:00Z",
        )


@pytest.mark.asyncio
async def test_crypto_tool_openai_schema():
    tool = CryptoTool()
    schema = tool.to_openai_tool()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "get_crypto_summary"
    params = schema["function"]["parameters"]
    assert "coin_id" in params["properties"]
    assert "coin_id" in params["required"]


@pytest.mark.asyncio
async def test_crypto_tool_mock_execution():
    mock_provider = MockCryptoProvider()
    tool = CryptoTool(provider=mock_provider)

    result = await tool.execute_with_resilience(coin_id="bitcoin", vs_currency="usd")
    assert result.success is True
    assert result.data is not None
    assert result.data["symbol"] == "BTC"
    assert result.data["current_price"] == 83500.0
    assert result.data["price_change_24h_percent"] == -1.25
    assert result.provider == "mock_crypto"
    assert result.cached is False


@pytest.mark.asyncio
async def test_crypto_tool_caching():
    mock_provider = MockCryptoProvider()
    tool = CryptoTool(provider=mock_provider)

    # First call - cache miss
    result1 = await tool.execute(coin_id="ethereum", vs_currency="usd")
    assert result1.success is True
    assert result1.cached is False

    # Second call - cache hit
    result2 = await tool.execute(coin_id="ethereum", vs_currency="usd")
    assert result2.success is True
    assert result2.cached is True
    assert result2.data["current_price"] == 2700.0


@pytest.mark.asyncio
async def test_crypto_tool_invalid_coin():
    mock_provider = MockCryptoProvider()
    tool = CryptoTool(provider=mock_provider)

    result = await tool.execute(coin_id="nonexistentcoin999")
    assert result.success is False
    assert "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_crypto_tool_validation():
    tool = CryptoTool()
    # Missing required 'coin_id'
    result = await tool.execute()
    assert result.success is False
    assert "Invalid arguments" in result.error


@pytest.mark.asyncio
async def test_agent_router_crypto_fallback():
    router = AgentRouter()
    answer, tools = await router.run("What is the price of Bitcoin right now?")
    assert len(tools) == 1
    assert tools[0].tool_name == "get_crypto_summary"
    assert "Bitcoin" in answer
    assert "BTC" in answer
    assert "Current Price" in answer
