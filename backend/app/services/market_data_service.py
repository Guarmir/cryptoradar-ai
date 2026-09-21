import time

import requests
from fastapi import HTTPException


COINGECKO_API = "https://api.coingecko.com/api/v3"

COIN_LIST_TTL = 60 * 60
MARKET_TTL = 60
CHART_TTL = 60 * 5


PREFERRED_ALIASES = {
    "btc": "bitcoin",
    "xbt": "bitcoin",
    "bitcoin": "bitcoin",
    "eth": "ethereum",
    "ethereum": "ethereum",
    "sol": "solana",
    "solana": "solana",
    "xrp": "ripple",
    "ripple": "ripple",
    "ada": "cardano",
    "cardano": "cardano",
    "doge": "dogecoin",
    "dogecoin": "dogecoin",
    "bnb": "binancecoin",
    "matic": "matic-network",
    "avax": "avalanche-2",
    "link": "chainlink",
    "dot": "polkadot",
    "ltc": "litecoin",
    "trx": "tron",
    "shib": "shiba-inu",
    "uni": "uniswap",
    "atom": "cosmos",
    "etc": "ethereum-classic",
    "xlm": "stellar",
    "bch": "bitcoin-cash",
    "near": "near",
    "apt": "aptos",
    "arb": "arbitrum",
    "op": "optimism",
    "pepe": "pepe",
}


coin_list_cache = {
    "data": None,
    "timestamp": 0,
}

market_cache = {}
chart_cache = {}


def get_cached(
    cache_dict,
    key,
    ttl,
):
    item = cache_dict.get(key)

    if not item:
        return None

    if time.time() - item["timestamp"] > ttl:
        return None

    return item["data"]


def set_cached(
    cache_dict,
    key,
    data,
):
    cache_dict[key] = {
        "data": data,
        "timestamp": time.time(),
    }


def get_coin_list():
    cached = coin_list_cache["data"]

    if (
        cached
        and (
            time.time()
            - coin_list_cache["timestamp"]
            <= COIN_LIST_TTL
        )
    ):
        return cached

    url = f"{COINGECKO_API}/coins/list"

    try:
        response = requests.get(
            url,
            timeout=20,
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Erro ao buscar lista "
                    "de moedas."
                ),
            )

        data = response.json()

        coin_list_cache["data"] = data
        coin_list_cache["timestamp"] = (
            time.time()
        )

        return data

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Erro ao buscar lista "
                "de moedas."
            ),
        ) from error


def resolve_coin_id(
    user_input: str,
):
    query = user_input.strip().lower()

    if not query:
        return None

    if query in PREFERRED_ALIASES:
        return PREFERRED_ALIASES[query]

    coins = get_coin_list()

    for coin in coins:
        if coin["id"].lower() == query:
            return coin["id"]

    for coin in coins:
        if coin["name"].lower() == query:
            return coin["id"]

    exact_symbol_matches = [
        coin
        for coin in coins
        if coin["symbol"].lower() == query
    ]

    if exact_symbol_matches:
        if len(exact_symbol_matches) == 1:
            return exact_symbol_matches[0]["id"]

        preferred_names = {
            "btc": "bitcoin",
            "eth": "ethereum",
            "sol": "solana",
            "xrp": "ripple",
            "ada": "cardano",
            "doge": "dogecoin",
        }

        preferred_name = (
            preferred_names.get(query)
        )

        if preferred_name:
            for coin in exact_symbol_matches:
                if (
                    coin["id"].lower()
                    == preferred_name
                    or coin["name"].lower()
                    == preferred_name
                ):
                    return coin["id"]

        return exact_symbol_matches[0]["id"]

    for coin in coins:
        if query in coin["id"].lower():
            return coin["id"]

    for coin in coins:
        if query in coin["name"].lower():
            return coin["id"]

    return None


def get_market_data(
    coin_id: str,
):
    cached = get_cached(
        market_cache,
        coin_id,
        MARKET_TTL,
    )

    if cached:
        return cached

    url = (
        f"{COINGECKO_API}/coins/markets"
    )

    params = {
        "vs_currency": "usd",
        "ids": coin_id,
        "price_change_percentage": "24h",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=20,
        )

        if response.status_code != 200:
            return None

        data = response.json()

        if not data:
            return None

        market = data[0]

        set_cached(
            market_cache,
            coin_id,
            market,
        )

        return market

    except Exception:
        return None


def get_chart_data(
    coin_id: str,
    days: int,
):
    cache_key = f"{coin_id}_{days}"

    cached = get_cached(
        chart_cache,
        cache_key,
        CHART_TTL,
    )

    if cached:
        return cached

    url = (
        f"{COINGECKO_API}"
        f"/coins/{coin_id}/market_chart"
    )

    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": (
            "hourly"
            if days <= 7
            else "daily"
        ),
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=20,
        )

        if response.status_code != 200:
            return {
                "prices": [],
            }

        data = response.json()

        set_cached(
            chart_cache,
            cache_key,
            data,
        )

        return data

    except Exception:
        return {
            "prices": [],
        }


def safe_float(value):
    try:
        if value is None:
            return 0.0

        return float(value)

    except Exception:
        return 0.0