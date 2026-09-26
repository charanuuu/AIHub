import abc
import asyncio
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from app.core.logging import logger


class ToolResult(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    cached: bool = False
    provider: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "cached": self.cached,
            "provider": self.provider,
        }


class BaseTool(abc.ABC):
    """
    Abstract base class for all AI tools in AI Hub.
    Guarantees strict schema, timeouts, retries, and modular provider abstraction.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique identifier for the tool (e.g. 'get_weather')."""
        pass

    @property
    @abc.abstractmethod
    def category(self) -> str:
        """Category (e.g. 'Weather', 'Finance', 'Crypto', 'News', 'Currency')."""
        pass

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Clear description for the AI agent to know when and how to call this tool."""
        pass

    @property
    @abc.abstractmethod
    def parameters_schema(self) -> Dict[str, Any]:
        """JSON schema defining the exact input parameters accepted by this tool."""
        pass

    @property
    def default_timeout_seconds(self) -> float:
        return 8.0

    @property
    def max_retries(self) -> int:
        return 2

    def to_openai_tool(self) -> Dict[str, Any]:
        """Export tool definition in OpenAI function-calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }

    async def execute_with_resilience(self, **kwargs) -> ToolResult:
        """
        Executes the tool with timeout control, retries, and graceful error handling.
        """
        start_time = time.perf_counter()
        last_error = ""

        for attempt in range(1, self.max_retries + 1):
            try:
                # Run execution wrapped in timeout
                result = await asyncio.wait_for(
                    self.execute(**kwargs), timeout=self.default_timeout_seconds
                )
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                result.execution_time_ms = round(elapsed_ms, 2)
                return result

            except asyncio.TimeoutError:
                last_error = f"Request timed out after {self.default_timeout_seconds}s"
                logger.warning(
                    f"Tool '{self.name}' attempt {attempt}/{self.max_retries} timed out."
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Tool '{self.name}' attempt {attempt}/{self.max_retries} failed: {e}"
                )

            if attempt < self.max_retries:
                # Exponential backoff: 0.5s, 1.0s...
                await asyncio.sleep(0.5 * (2 ** (attempt - 1)))

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return ToolResult(
            success=False,
            error=f"Tool '{self.name}' failed after {self.max_retries} attempts: {last_error}",
            execution_time_ms=round(elapsed_ms, 2),
        )

    @abc.abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Core tool implementation to be provided by subclasses."""
        pass
