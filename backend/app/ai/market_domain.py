from enum import Enum


class MarketDomain(
    str,
    Enum,
):
    CRYPTO = "crypto"
    STOCKS = "stocks"
    FOREX = "forex"
    COMMODITIES = "commodities"