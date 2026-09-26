import json
import re
from typing import Any, Dict, List, Optional
import httpx
from openai import AsyncOpenAI
from app.agent.prompts import SYSTEM_PROMPT
from app.core.config import settings
from app.core.logging import logger
from app.models.schemas import ToolCallDetail
from app.tools.base import ToolResult
from app.tools.registry import tool_registry


class AgentRouter:
    """
    Manages the AI conversation loop and routes tool execution calls.
    """

    def __init__(self):
        self._openai_client: Optional[AsyncOpenAI] = None
        self._init_openai_client()

    def _init_openai_client(self):
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip() not in (
            "",
            "your_openai_api_key_here",
        ):
            try:
                self._openai_client = AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL or None,
                    timeout=httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS * 2),
                )
                logger.info("OpenAI client initialized successfully.")
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {e}")
                self._openai_client = None
        else:
            logger.info(
                "OPENAI_API_KEY not configured. Agent will use deterministic fallback routing for tools."
            )
            self._openai_client = None

    async def run(
        self,
        user_message: str,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> tuple[str, List[ToolCallDetail]]:
        """
        Runs the agent loop. Returns (final_answer, list_of_executed_tools).
        """
        # If OpenAI client is available, use official function calling loop
        if self._openai_client is not None:
            try:
                return await self._run_openai_agent(user_message, history)
            except Exception as e:
                logger.error(f"OpenAI agent execution failed: {e}. Falling back to deterministic router.")

        # Fallback to local intelligent rule-based tool router
        return await self._run_local_fallback(user_message)

    async def _run_openai_agent(
        self,
        user_message: str,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> tuple[str, List[ToolCallDetail]]:
        assert self._openai_client is not None

        messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Append previous conversation history if available
        if history:
            for item in history:
                messages.append(
                    {
                        "role": item.get("role", "user"),
                        "content": item.get("content", ""),
                    }
                )

        # Append the new user message
        messages.append({"role": "user", "content": user_message})

        tools_def = tool_registry.get_openai_tools()
        executed_tools: List[ToolCallDetail] = []

        for iteration in range(settings.AGENT_MAX_ITERATIONS):
            logger.info(f"Agent iteration {iteration + 1}/{settings.AGENT_MAX_ITERATIONS}")

            response = await self._openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                tools=tools_def if tools_def else None,
                tool_choice="auto" if tools_def else None,
                temperature=settings.AGENT_TEMPERATURE,
            )

            choice = response.choices[0]
            message = choice.message

            # Check if model requested tool call(s)
            if message.tool_calls:
                # Add assistant message with tool calls to history
                messages.append(message.model_dump())

                for tool_call in message.tool_calls:
                    fn_name = tool_call.function.name
                    raw_args = tool_call.function.arguments
                    try:
                        args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    except Exception:
                        args = {}

                    logger.info(f"AI requested tool call: {fn_name}({args})")

                    # Execute the tool safely via registry
                    tool_result: ToolResult = await tool_registry.execute_tool(
                        fn_name, **args
                    )

                    tool_detail = ToolCallDetail(
                        tool_name=fn_name,
                        arguments=args,
                        result=tool_result.data,
                        success=tool_result.success,
                        error=tool_result.error,
                        execution_time_ms=tool_result.execution_time_ms,
                    )
                    executed_tools.append(tool_detail)

                    # Append tool result to context
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(
                                tool_result.data
                                if tool_result.success
                                else {"error": tool_result.error}
                            ),
                        }
                    )
                # Next loop iteration allows model to synthesize tool output
                continue

            # Model produced a final textual response
            final_content = message.content or "No response generated."
            return final_content, executed_tools

        return "I processed your request, but exceeded the maximum tool call limit.", executed_tools

    async def _run_local_fallback(
        self, user_message: str
    ) -> tuple[str, List[ToolCallDetail]]:
        """
        Deterministic local router that detects weather intent,
        calls the live WeatherTool, and generates structured responses.
        Works seamlessly without requiring an OpenAI API key.
        """
        executed_tools: List[ToolCallDetail] = []
        msg_lower = user_message.lower()

        # Check if the query is asking about weather
        weather_keywords = ["weather", "temperature", "forecast", "rain", "sunny", "humid", "cloudy", "degrees"]
        if any(kw in msg_lower for kw in weather_keywords):
            city = self._extract_city_from_query(user_message) or "Bangalore"
            days = 2 if any(w in msg_lower for w in ["tomorrow", "2 days", "two days"]) else 1

            logger.info(f"Fallback router: detected weather intent for city='{city}', days={days}")
            tool_result = await tool_registry.execute_tool("get_weather", city=city, days=days)

            tool_detail = ToolCallDetail(
                tool_name="get_weather",
                arguments={"city": city, "days": days, "unit": "celsius"},
                result=tool_result.data,
                success=tool_result.success,
                error=tool_result.error,
                execution_time_ms=tool_result.execution_time_ms,
            )
            executed_tools.append(tool_detail)

            if tool_result.success and tool_result.data:
                d = tool_result.data
                cur = d.get("current", {})
                city_name = d.get("city", city)
                country = d.get("country", "")
                temp = cur.get("temperature", 0)
                feels = cur.get("feels_like", 0)
                cond = cur.get("condition", "Clear")
                humid = cur.get("humidity", 0)
                wind = cur.get("wind_speed", 0)
                unit = "°C" if d.get("unit") == "celsius" else "°F"

                response_text = (
                    f"### Weather in {city_name}"
                    + (f", {country}\n\n" if country else "\n\n")
                    + f"- **Condition:** {cond}\n"
                    + f"- **Temperature:** {temp}{unit} (Feels like {feels}{unit})\n"
                    + f"- **Humidity:** {humid}%\n"
                    + f"- **Wind Speed:** {wind} km/h\n"
                )

                forecast = d.get("forecast", [])
                if len(forecast) > 1:
                    tmrw = forecast[1]
                    response_text += (
                        f"\n**Tomorrow's Forecast ({tmrw.get('date')}):**\n"
                        f"- Condition: {tmrw.get('condition')}\n"
                        f"- High: {tmrw.get('max_temperature')}{unit} | Low: {tmrw.get('min_temperature')}{unit}\n"
                    )

                response_text += f"\n*(Data retrieved live from {tool_result.provider})*"
                return response_text, executed_tools
            else:
                return (
                    f"I couldn't retrieve the weather for '{city}'. Error: {tool_result.error}",
                    executed_tools,
                )

        # Check if the query is asking about currency exchange / conversion
        currency_match = self._extract_currency_conversion(user_message)
        if currency_match:
            amount, from_curr, to_curr = currency_match
            logger.info(f"Fallback router: detected currency intent for {amount} {from_curr}->{to_curr}")
            tool_result = await tool_registry.execute_tool(
                "convert_currency",
                amount=amount,
                from_currency=from_curr,
                to_currency=to_curr,
            )

            tool_detail = ToolCallDetail(
                tool_name="convert_currency",
                arguments={"amount": amount, "from_currency": from_curr, "to_currency": to_curr},
                result=tool_result.data,
                success=tool_result.success,
                error=tool_result.error,
                execution_time_ms=tool_result.execution_time_ms,
            )
            executed_tools.append(tool_detail)

            if tool_result.success and tool_result.data:
                d = tool_result.data
                orig_amt = d.get("amount", amount)
                conv_amt = d.get("converted_amount", 0.0)
                rate = d.get("exchange_rate", 0.0)
                date_str = d.get("date", "")

                response_text = (
                    f"### Currency Conversion\n\n"
                    f"- **Original Amount:** {orig_amt:,.2f} {from_curr}\n"
                    f"- **Converted Amount:** **{conv_amt:,.2f} {to_curr}**\n"
                    f"- **Exchange Rate:** 1 {from_curr} = {rate:.6f} {to_curr}\n"
                )
                if date_str:
                    response_text += f"- **Rate Date:** {date_str}\n"

                response_text += f"\n*(Data retrieved live from {tool_result.provider})*"
                return response_text, executed_tools
            else:
                return (
                    f"I couldn't perform the currency conversion from {from_curr} to {to_curr}. Error: {tool_result.error}",
                    executed_tools,
                )

        # Check if the query is asking about cryptocurrency
        crypto_match = self._extract_crypto_query(user_message)
        if crypto_match:
            coin_id, vs_currency = crypto_match
            logger.info(f"Fallback router: detected crypto intent for coin='{coin_id}', vs='{vs_currency}'")
            tool_result = await tool_registry.execute_tool(
                "get_crypto_summary",
                coin_id=coin_id,
                vs_currency=vs_currency,
            )

            tool_detail = ToolCallDetail(
                tool_name="get_crypto_summary",
                arguments={"coin_id": coin_id, "vs_currency": vs_currency},
                result=tool_result.data,
                success=tool_result.success,
                error=tool_result.error,
                execution_time_ms=tool_result.execution_time_ms,
            )
            executed_tools.append(tool_detail)

            if tool_result.success and tool_result.data:
                d = tool_result.data
                name = d.get("name", coin_id.capitalize())
                symbol = d.get("symbol", coin_id.upper())
                price = d.get("current_price", 0.0)
                change = d.get("price_change_24h_percent")
                mcap = d.get("market_cap")
                high = d.get("high_24h")
                low = d.get("low_24h")
                vs_curr = d.get("vs_currency", vs_currency.upper())

                change_str = f"{'+' if change and change > 0 else ''}{change:.2f}%" if change is not None else "N/A"

                response_text = (
                    f"### {name} ({symbol}) Market Summary\n\n"
                    f"- **Current Price:** **${price:,.2f} {vs_curr}**\n"
                    f"- **24h Price Change:** {change_str}\n"
                )
                if mcap:
                    response_text += f"- **Market Cap:** ${mcap:,.0f}\n"
                if high is not None and low is not None:
                    response_text += f"- **24h Range:** High ${high:,.2f} | Low ${low:,.2f}\n"

                response_text += f"\n*(Data retrieved live from {tool_result.provider})*"
                return response_text, executed_tools
            else:
                return (
                    f"I couldn't retrieve cryptocurrency data for '{coin_id}'. Error: {tool_result.error}",
                    executed_tools,
                )

        # Check if the query is asking about stock market / finance quotes
        finance_match = self._extract_finance_query(user_message)
        if finance_match:
            symbol = finance_match
            logger.info(f"Fallback router: detected finance intent for symbol='{symbol}'")
            tool_result = await tool_registry.execute_tool(
                "get_market_quote",
                symbol=symbol,
            )

            tool_detail = ToolCallDetail(
                tool_name="get_market_quote",
                arguments={"symbol": symbol},
                result=tool_result.data,
                success=tool_result.success,
                error=tool_result.error,
                execution_time_ms=tool_result.execution_time_ms,
            )
            executed_tools.append(tool_detail)

            if tool_result.success and tool_result.data:
                d = tool_result.data
                name = d.get("name") or symbol
                sym = d.get("symbol", symbol)
                price = d.get("price", 0.0)
                change = d.get("change")
                change_pct = d.get("change_percent")
                high = d.get("day_high")
                low = d.get("day_low")
                vol = d.get("volume")
                curr = d.get("currency", "USD")
                exchange = d.get("exchange")

                change_str = ""
                if change is not None and change_pct is not None:
                    sign = "+" if change >= 0 else ""
                    change_str = f"{sign}${change:,.2f} ({sign}{change_pct:.2f}%)"
                elif change_pct is not None:
                    sign = "+" if change_pct >= 0 else ""
                    change_str = f"{sign}{change_pct:.2f}%"

                response_text = (
                    f"### {name} ({sym}) Market Quote\n\n"
                    f"- **Current Price:** **${price:,.2f} {curr}**\n"
                )
                if change_str:
                    response_text += f"- **Daily Change:** {change_str}\n"
                if high is not None and low is not None:
                    response_text += f"- **Day Range:** High ${high:,.2f} | Low ${low:,.2f}\n"
                if vol:
                    response_text += f"- **Volume:** {vol:,}\n"
                if exchange:
                    response_text += f"- **Exchange:** {exchange}\n"

                response_text += f"\n*(Data retrieved live from {tool_result.provider})*"
                return response_text, executed_tools
            else:
                return (
                    f"I couldn't retrieve market data for '{symbol}'. Error: {tool_result.error}",
                    executed_tools,
                )

        # Check if the query is asking about news / headlines
        news_match = self._extract_news_query(user_message)
        if news_match:
            query_param, category_param = news_match
            logger.info(f"Fallback router: detected news intent query='{query_param}', category='{category_param}'")
            tool_result = await tool_registry.execute_tool(
                "get_latest_news",
                query=query_param,
                category=category_param,
                limit=5,
            )

            tool_detail = ToolCallDetail(
                tool_name="get_latest_news",
                arguments={"query": query_param, "category": category_param, "limit": 5},
                result=tool_result.data,
                success=tool_result.success,
                error=tool_result.error,
                execution_time_ms=tool_result.execution_time_ms,
            )
            executed_tools.append(tool_detail)

            if tool_result.success and tool_result.data:
                d = tool_result.data
                topic = d.get("topic", "News")
                articles = d.get("articles", [])

                response_text = f"### Latest {topic} Headlines\n\n"
                for i, art in enumerate(articles, 1):
                    t = art.get("title", "")
                    src = art.get("source", "")
                    url = art.get("url")
                    dt = art.get("published_at")

                    response_text += f"{i}. **{t}**\n"
                    meta_parts = []
                    if src:
                        meta_parts.append(f"*Source:* {src}")
                    if dt:
                        meta_parts.append(f"*Date:* {dt}")
                    if meta_parts:
                        response_text += f"   - {' | '.join(meta_parts)}\n"
                    if url:
                        response_text += f"   - [Read Full Article]({url})\n"
                    response_text += "\n"

                response_text += f"*(Data retrieved live from {tool_result.provider})*"
                return response_text, executed_tools
            else:
                return (
                    f"I couldn't retrieve news headlines. Error: {tool_result.error}",
                    executed_tools,
                )

        # Generic greetings or other topics
        if any(g in msg_lower for g in ["hi", "hello", "hey"]):
            return (
                "Hello! I am your AI Hub assistant. I can fetch real-time information using 5 live tools:\n"
                "- **Weather:** *What is the weather in Bangalore tomorrow?*\n"
                "- **Currency:** *Convert 50,000 INR to USD*\n"
                "- **Crypto:** *What is the price of Bitcoin?*\n"
                "- **Finance:** *Apple stock price*\n"
                "- **News:** *Latest technology news*",
                [],
            )

        return (
            f"I received your request: '{user_message}'. "
            "All 5 real-time tools are active: Weather, Currency Exchange, Cryptocurrency, Stocks & Market Quotes, and News! "
            "Try asking 'What is the latest news in AI?' or 'Convert 100 EUR to USD'.",
            [],
        )

    def _extract_city_from_query(self, query: str) -> Optional[str]:
        # Regex patterns to extract city name
        patterns = [
            r"weather in\s+([A-Za-z\s]+?)(?:\s+tomorrow|\s+today|\s+next week|\?|$)",
            r"weather for\s+([A-Za-z\s]+?)(?:\s+tomorrow|\s+today|\?|$)",
            r"temperature in\s+([A-Za-z\s]+?)(?:\s+tomorrow|\s+today|\?|$)",
            r"forecast for\s+([A-Za-z\s]+?)(?:\s+tomorrow|\s+today|\?|$)",
            r"in\s+([A-Za-z\s]+?)\s+weather",
        ]
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                city = match.group(1).strip()
                if city:
                    return city

        # If simple single word or city query
        words = query.strip().split()
        if len(words) == 1 and words[0].isalpha():
            return words[0]

        return None

    def _extract_currency_conversion(self, query: str) -> Optional[tuple[float, str, str]]:
        symbol_map = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR"}
        clean = query.strip()

        # Check for currency symbols with amounts e.g. $50, ₹50000, €100
        # Pattern 1: "convert 50,000 INR to USD", "convert $50 to EUR"
        p1 = re.search(
            r"(?:convert|how much is|calculate)\s+([$€£¥₹]?\s*[\d,]+(?:\.\d+)?)\s*([A-Za-z]{3})?\s*(?:to|in|into)\s*([$€£¥₹]?\s*[A-Za-z]{3}|\$|€|£|¥|₹)",
            clean,
            re.IGNORECASE,
        )
        if p1:
            raw_amt_str = p1.group(1).replace(",", "").strip()
            from_curr = p1.group(2)
            to_curr = p1.group(3).strip()

            # Handle symbol in amount e.g. $50
            for sym, code in symbol_map.items():
                if sym in raw_amt_str:
                    raw_amt_str = raw_amt_str.replace(sym, "").strip()
                    if not from_curr:
                        from_curr = code
                if sym in to_curr:
                    to_curr = code

            try:
                amount = float(raw_amt_str)
            except ValueError:
                amount = 1.0

            if from_curr and to_curr:
                return amount, from_curr.upper(), to_curr.upper()

        # Pattern 2: "50,000 INR to USD" or "100 EUR in JPY"
        p2 = re.search(
            r"([\d,]+(?:\.\d+)?)\s*([A-Za-z]{3})\s*(?:to|in|into)\s*([A-Za-z]{3})",
            clean,
            re.IGNORECASE,
        )
        if p2:
            try:
                amt = float(p2.group(1).replace(",", ""))
                return amt, p2.group(2).upper(), p2.group(3).upper()
            except ValueError:
                pass

        # Pattern 3: "USD to INR", "USD/INR", "exchange rate of USD to EUR"
        p3 = re.search(
            r"(?:rate of|exchange rate of|rate for)?\s*([A-Za-z]{3})\s*(?:to|/)\s*([A-Za-z]{3})",
            clean,
            re.IGNORECASE,
        )
        if p3 and ("rate" in clean.lower() or "exchange" in clean.lower() or "convert" in clean.lower() or "/" in clean):
            return 1.0, p3.group(1).upper(), p3.group(2).upper()

        return None

    def _extract_crypto_query(self, query: str) -> Optional[tuple[str, str]]:
        q_lower = query.lower()

        known_crypto = [
            "bitcoin", "btc", "ethereum", "eth", "solana", "sol",
            "dogecoin", "doge", "cardano", "ada", "ripple", "xrp",
            "binancecoin", "bnb", "polkadot", "dot", "avalanche", "avax",
            "chainlink", "link", "polygon", "matic", "shiba inu", "shib",
            "litecoin", "ltc"
        ]

        found_coin = None
        # Check longer names first so 'bitcoin' matches before 'bit', 'ethereum' before 'eth'
        for coin in sorted(known_crypto, key=len, reverse=True):
            # match as whole word
            pattern = rf"\b{coin}\b"
            if re.search(pattern, q_lower):
                found_coin = coin
                break

        if not found_coin:
            # Check pattern: "price of <word>" or "<word> price" when words like 'crypto' are present
            if "crypto" in q_lower:
                m = re.search(r"(?:crypto\s+price\s+of|price\s+of\s+crypto|crypto\s+summary\s+for|crypto)\s+([A-Za-z0-9_-]+)", q_lower)
                if m and m.group(1) not in ("market", "summary", "price", "trend", "the"):
                    found_coin = m.group(1)

        if not found_coin:
            if "crypto" in q_lower and any(w in q_lower for w in ["summary", "market", "overview", "trends", "rates", "prices"]):
                found_coin = "bitcoin"

        if not found_coin:
            return None

        # Determine vs_currency (default usd)
        vs_currency = "usd"
        for curr in ["inr", "eur", "gbp", "jpy", "cad", "aud", "usd"]:
            if re.search(rf"\b(?:in|to)\s+{curr}\b", q_lower) or re.search(rf"\b{curr}\b", q_lower):
                vs_currency = curr
                break

        return found_coin, vs_currency

    def _extract_finance_query(self, query: str) -> Optional[str]:
        q = query.strip()
        q_lower = q.lower()

        # Check for parenthesized symbol: (AAPL), (TSLA)
        paren_tag = re.search(r"\(([A-Za-z]{1,5})\)", q)
        if paren_tag:
            return paren_tag.group(1).upper()

        # Check for ticker with cash tag: $AAPL, $TSLA, $NVDA
        cash_tag = re.search(r"\$([A-Za-z]{1,5})\b", q)
        if cash_tag:
            return cash_tag.group(1).upper()

        # Pattern: "stock price of AAPL", "quote for Tesla", "shares of NVDA"
        p1 = re.search(
            r"(?:stock price of|price of stock|quote for|stock quote for|stock of|share price of|shares of|stock price for)\s+([A-Za-z0-9\.\^\s]+?)(?:\?|$|\.|\s+today)",
            q,
            re.IGNORECASE,
        )
        if p1:
            raw = p1.group(1).strip()
            if raw and raw.lower() not in ("the", "a", "an"):
                return raw

        # Pattern: "Apple stock price", "Tesla stock", "TSLA quote"
        p2 = re.search(
            r"([A-Za-z0-9\.\^]+)\s+(?:stock price|stock quote|stock|shares|equity quote)",
            q,
            re.IGNORECASE,
        )
        if p2:
            sym = p2.group(1).strip()
            if sym.lower() not in ("the", "a", "an", "is", "of", "what"):
                return sym

        # Pattern: "how is AAPL doing", "how's Tesla stock"
        p3 = re.search(
            r"(?:how is|how's)\s+([A-Za-z0-9\.\^]+)\s+(?:doing|stock|trading)",
            q,
            re.IGNORECASE,
        )
        if p3:
            return p3.group(1).strip()

        # Popular companies if user asks about their market price/quote
        popular = ["apple", "tesla", "microsoft", "google", "amazon", "nvidia", "meta", "netflix", "sp500", "s&p 500"]
        if any(w in q_lower for w in ["market", "quote", "price", "share", "value", "stock"]):
            for comp in popular:
                if re.search(rf"\b{comp}\b", q_lower):
                    return comp

        return None

    def _extract_news_query(self, query: str) -> Optional[tuple[Optional[str], str]]:
        q = query.strip()
        q_lower = q.lower()

        if not any(k in q_lower for k in ["news", "headline", "headlines", "breaking"]):
            return None

        # Check for category matches first
        categories = {
            "technology": ["technology", "tech"],
            "business": ["business", "finance", "financial", "economy", "market news"],
            "science": ["science", "space", "astronomy"],
            "health": ["health", "medical", "medicine"],
            "sports": ["sports", "sport", "football", "cricket", "nba"],
            "entertainment": ["entertainment", "celebrity", "movie", "hollywood", "bollywood"],
        }

        matched_category = "general"
        for cat, synonyms in categories.items():
            if any(re.search(rf"\b{syn}\b", q_lower) for syn in synonyms):
                matched_category = cat
                break

        # Check for specific search query: "news about X", "news on X", "news regarding X"
        p1 = re.search(
            r"(?:news\s+about|news\s+on|news\s+regarding|headlines\s+about|headlines\s+on)\s+([A-Za-z0-9\s_-]+?)(?:\?|$|\.|\s+today)",
            q,
            re.IGNORECASE,
        )
        if p1:
            topic = p1.group(1).strip()
            if topic and topic.lower() not in ("the", "a", "an", "all", "today"):
                return topic, matched_category

        # Check: "X news" e.g. "AI news", "Google news", "Tesla news"
        p2 = re.search(
            r"([A-Za-z0-9\s_-]+?)\s+(?:news|headlines)",
            q,
            re.IGNORECASE,
        )
        if p2:
            candidate = p2.group(1).strip()
            # If candidate is not just a generic modifier like 'latest', 'today', 'top', or a category name
            modifiers = {"latest", "top", "breaking", "today", "current", "world", "local", "global"}
            words = candidate.lower().split()
            filtered_words = [w for w in words if w not in modifiers and not any(w in syns for syns in categories.values())]
            if filtered_words:
                return " ".join(filtered_words), matched_category

        return None, matched_category


agent_router = AgentRouter()
