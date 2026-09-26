from typing import Any, Dict, List, Optional
from app.core.logging import logger
from app.models.schemas import ToolInfo
from app.tools.base import BaseTool, ToolResult
from app.tools.weather.tool import WeatherTool
from app.tools.currency.tool import CurrencyExchangeTool
from app.tools.crypto.tool import CryptoTool
from app.tools.finance.tool import FinanceTool
from app.tools.news.tool import NewsTool


class ToolRegistry:
    """
    Central registry for all AI Hub external tools.
    Manages registration, schema generation, and safe execution.
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        # Register production tools
        self.register(WeatherTool())
        self.register(CurrencyExchangeTool())
        self.register(CryptoTool())
        self.register(FinanceTool())
        self.register(NewsTool())
        logger.info("Default tools registered successfully.")

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            logger.warning(f"Overwriting existing tool registration: '{tool.name}'")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool '{tool.name}' in category '{tool.category}'")

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolInfo]:
        results: List[ToolInfo] = []
        for tool in self._tools.values():
            provider_name = (
                getattr(tool, "_provider", None).provider_name
                if hasattr(tool, "_provider") and hasattr(tool._provider, "provider_name")
                else "native"
            )
            results.append(
                ToolInfo(
                    name=tool.name,
                    category=tool.category,
                    description=tool.description,
                    parameters=tool.parameters_schema,
                    status="active",
                    provider=provider_name,
                )
            )

        # Include upcoming planned tools so Flutter UI displays tool categories/shortcuts
        planned_tools = [
            ("get_crypto_summary", "Cryptocurrency", "Real-time cryptocurrency quotes, price changes, and 24h market trends.", "planned"),
            ("get_market_quote", "Finance", "Stock market equity quotes, indices, and financial market data.", "planned"),
            ("get_latest_news", "News", "Latest verified news headlines across topics and categories.", "planned"),
            ("convert_currency", "Currency", "Live foreign exchange rates and currency conversion calculator.", "planned"),
        ]
        for name, category, desc, status in planned_tools:
            if name not in self._tools:
                results.append(
                    ToolInfo(
                        name=name,
                        category=category,
                        description=desc,
                        parameters={},
                        status=status,
                        provider="provider_pipeline",
                    )
                )

        return results

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """Returns active tools formatted for OpenAI function calling."""
        return [tool.to_openai_tool() for tool in self._tools.values()]

    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' is not registered or not currently available.",
            )
        return await tool.execute_with_resilience(**kwargs)


tool_registry = ToolRegistry()
