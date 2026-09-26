COMPANY_TO_TICKER = {
    "apple": "AAPL",
    "tesla": "TSLA",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "microsoft": "MSFT",
    "amazon": "AMZN",
    "nvidia": "NVDA",
    "meta": "META",
    "facebook": "META",
    "netflix": "NFLX",
    "amd": "AMD",
    "intel": "INTC",
    "ibm": "IBM",
    "uber": "UBER",
    "airbnb": "ABNB",
    "oracle": "ORCL",
    "salesforce": "CRM",
    "cisco": "CSCO",
    "adobe": "ADBE",
    "disney": "DIS",
    "coca cola": "KO",
    "coke": "KO",
    "pepsi": "PEP",
    "walmart": "WMT",
    "sp500": "SPY",
    "s&p 500": "SPY",
    "s&p": "SPY",
    "nasdaq": "QQQ",
    "dow": "DIA",
    "dow jones": "DIA",
    "reliance": "RELIANCE.NS",
    "tcs": "TCS.NS",
    "infosys": "INFY",
    "tata motors": "TATAMOTORS.NS",
    "hdfc": "HDFCBANK.NS",
}


def resolve_ticker_symbol(query: str) -> str:
    """
    Resolves company names or tickers to standard ticker symbols.
    """
    clean = query.strip().lower()
    if clean in COMPANY_TO_TICKER:
        return COMPANY_TO_TICKER[clean]

    # Remove '$' if present, e.g. '$AAPL' -> 'AAPL'
    clean = clean.lstrip("$").strip()
    if clean in COMPANY_TO_TICKER:
        return COMPANY_TO_TICKER[clean]

    # Return uppercase ticker
    return query.lstrip("$").strip().upper()
