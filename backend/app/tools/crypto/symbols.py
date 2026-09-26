from typing import Tuple

# Mapping: alias -> (coingecko_id, binance_symbol, display_name, display_ticker)
CRYPTO_ALIASES = {
    "btc": ("bitcoin", "BTCUSDT", "Bitcoin", "BTC"),
    "bitcoin": ("bitcoin", "BTCUSDT", "Bitcoin", "BTC"),
    "eth": ("ethereum", "ETHUSDT", "Ethereum", "ETH"),
    "ethereum": ("ethereum", "ETHUSDT", "Ethereum", "ETH"),
    "sol": ("solana", "SOLUSDT", "Solana", "SOL"),
    "solana": ("solana", "SOLUSDT", "Solana", "SOL"),
    "doge": ("dogecoin", "DOGEUSDT", "Dogecoin", "DOGE"),
    "dogecoin": ("dogecoin", "DOGEUSDT", "Dogecoin", "DOGE"),
    "xrp": ("ripple", "XRPUSDT", "XRP", "XRP"),
    "ripple": ("ripple", "XRPUSDT", "XRP", "XRP"),
    "ada": ("cardano", "ADAUSDT", "Cardano", "ADA"),
    "cardano": ("cardano", "ADAUSDT", "Cardano", "ADA"),
    "bnb": ("binancecoin", "BNBUSDT", "BNB", "BNB"),
    "binance": ("binancecoin", "BNBUSDT", "BNB", "BNB"),
    "binancecoin": ("binancecoin", "BNBUSDT", "BNB", "BNB"),
    "dot": ("polkadot", "DOTUSDT", "Polkadot", "DOT"),
    "polkadot": ("polkadot", "DOTUSDT", "Polkadot", "DOT"),
    "avax": ("avalanche-2", "AVAXUSDT", "Avalanche", "AVAX"),
    "avalanche": ("avalanche-2", "AVAXUSDT", "Avalanche", "AVAX"),
    "link": ("chainlink", "LINKUSDT", "Chainlink", "LINK"),
    "chainlink": ("chainlink", "LINKUSDT", "Chainlink", "LINK"),
    "matic": ("matic-network", "MATICUSDT", "Polygon", "MATIC"),
    "polygon": ("matic-network", "MATICUSDT", "Polygon", "MATIC"),
    "shib": ("shiba-inu", "SHIBUSDT", "Shiba Inu", "SHIB"),
    "shiba": ("shiba-inu", "SHIBUSDT", "Shiba Inu", "SHIB"),
    "ltc": ("litecoin", "LTCUSDT", "Litecoin", "LTC"),
    "litecoin": ("litecoin", "LTCUSDT", "Litecoin", "LTC"),
}


def resolve_crypto_symbol(query: str) -> Tuple[str, str, str, str]:
    """
    Returns (coingecko_id, binance_symbol, display_name, display_ticker)
    """
    key = query.lower().strip()
    if key in CRYPTO_ALIASES:
        return CRYPTO_ALIASES[key]

    # Default fallback: assume query is the coingecko id
    coingecko_id = key.replace(" ", "-")
    display_ticker = key.upper()
    display_name = key.capitalize()
    binance_symbol = f"{display_ticker}USDT"
    return coingecko_id, binance_symbol, display_name, display_ticker
