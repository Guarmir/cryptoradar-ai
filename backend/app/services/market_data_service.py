import logging
import time

import requests
from fastapi import HTTPException
from app.services.chart_request_cooldown import (
    ChartRequestCooldown,
)
from app.services.coingecko_request_runtime import (
    coingecko_request_coordinator,
)

from app.services.coingecko_request_coordinator import (
    CoinGeckoRequestBlocked,
)
from app.services.chart_data_cache import (
    ChartDataCache,
)
from app.services.coingecko_chart_client import (
    CoinGeckoChartClient,
    CoinGeckoChartRequestError,
)
from app.services.chart_acquisition_service import (
    ChartAcquisitionService,
)


logger = logging.getLogger(__name__)


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

chart_data_cache = ChartDataCache()

chart_cache = chart_data_cache.storage

chart_request_cooldown = (
    ChartRequestCooldown()
)

chart_client = CoinGeckoChartClient(
    api_base_url=COINGECKO_API,
    request_get=lambda *args, **kwargs: (
        coingecko_request_coordinator.execute(
            lambda: requests.get(
                *args,
                **kwargs,
            )
        )
    ),
)

chart_acquisition_service = (
    ChartAcquisitionService(
        chart_fetcher=chart_client.fetch,
    )
)


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
        response = coingecko_request_coordinator.execute(
            lambda: requests.get(
              url,
              timeout=20,
            )
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

    except CoinGeckoRequestBlocked as error:
        logger.warning(
            "CoinGecko coin list blocked: status_code=429 reason=%s",
            error,
        )

        if cached is not None:
            return cached

        raise HTTPException(
            status_code=503,
            detail="Lista de moedas temporariamente indisponível.",
        ) from error

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

    # Um ID canônico exato tem prioridade.
    for coin in coins:
        if coin["id"].lower() == query:
            return coin["id"]

    # Um nome exato também identifica
    # diretamente o ativo.
    for coin in coins:
        if coin["name"].lower() == query:
            return coin["id"]

    exact_symbol_matches = [
        coin
        for coin in coins
        if coin["symbol"].lower() == query
    ]

    # Símbolo só é considerado seguro quando
    # identifica exatamente um ativo.
    if len(exact_symbol_matches) == 1:
        return exact_symbol_matches[0]["id"]

    # Dois ou mais ativos com o mesmo símbolo
    # são considerados ambíguos.
    #
    # Não escolhemos silenciosamente o primeiro
    # resultado retornado pela CoinGecko.
    if len(exact_symbol_matches) > 1:
        return None

    for coin in coins:
        if query in coin["id"].lower():
            return coin["id"]

    for coin in coins:
        if query in coin["name"].lower():
            return coin["id"]

    return None

def get_market_data_batch(
    coin_ids: list[str],
) -> dict[str, dict]:
    normalized_ids = list(
        dict.fromkeys(
            coin_id.strip().lower()
            for coin_id in coin_ids
            if coin_id.strip()
        )
    )

    if not normalized_ids:
        return {}

    markets: dict[str, dict] = {}
    stale_markets: dict[str, dict] = {}
    missing_ids: list[str] = []

    for coin_id in normalized_ids:
        cached_item = market_cache.get(
            coin_id,
        )

        if cached_item:
            stale_data = cached_item.get(
                "data",
            )

            if stale_data:
                stale_markets[
                    coin_id
                ] = stale_data

        cached = get_cached(
            market_cache,
            coin_id,
            MARKET_TTL,
        )

        if cached:
            markets[coin_id] = cached
        else:
            missing_ids.append(
                coin_id,
            )

    if not missing_ids:
        return markets

    url = (
        f"{COINGECKO_API}/coins/markets"
    )

    params = {
        "vs_currency": "usd",
        "ids": ",".join(
            missing_ids
        ),
        "price_change_percentage": "24h",
    }

    try:
        response = coingecko_request_coordinator.execute(
            lambda: requests.get(
                url,
                params=params,
                timeout=20,
            )
        )

        if response.status_code != 200:
            logger.warning(
                "CoinGecko batch market request "
                "failed: coin_ids=%s "
                "status_code=%s",
                ",".join(missing_ids),
                response.status_code,
            )

            return {
                **stale_markets,
                **markets,
            }

        data = response.json()

        if not isinstance(data, list):
            return markets

        for market in data:
            if not isinstance(
                market,
                dict,
            ):
                continue

            coin_id = market.get("id")

            if not coin_id:
                continue

            markets[coin_id] = market

            set_cached(
                market_cache,
                coin_id,
                market,
            )

        return markets

    except Exception:
        return {
            **stale_markets,
            **markets,
        }


def get_market_data(
    coin_id: str,
):
    stale_cached = market_cache.get(
        coin_id,
    )

    stale_market = (
        stale_cached.get("data")
        if stale_cached
        else None
    )
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
        response = coingecko_request_coordinator.execute(
            lambda: requests.get(
               url,
               params=params,
               timeout=20,
            )
        )

        if response.status_code != 200:
            logger.warning(
                "CoinGecko market request failed: "
                "coin_id=%s status_code=%s",
                coin_id,
                response.status_code,
            )

            return stale_market

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

    except CoinGeckoRequestBlocked as error:
        logger.warning(
            "CoinGecko market request blocked: "
            "coin_id=%s status_code=429 reason=%s",
            coin_id,
            error,
        )
        return stale_market

    except Exception:
        return stale_market

def get_cached_chart_data(
    coin_id: str,
    days: int,
):
    return chart_data_cache.get(
        coin_id,
        days,
    )


def get_chart_data(
    coin_id: str,
    days: int,
):

    stale_chart = (
        chart_data_cache.get_stale(
            coin_id,
            days,
        )
    )

    cached = (
        chart_data_cache.get(
            coin_id,
            days,
        )
    )

    if cached:
        return cached

    if chart_request_cooldown.is_blocked():
        return stale_chart or {
            "prices": [],
        }

    try:
        data = chart_acquisition_service.fetch(
            coin_id,
            days,
        )

        chart_data_cache.set(
            coin_id,
            days,
            data,
        )

        return data

    except CoinGeckoRequestBlocked as error:
        chart_request_cooldown.activate()

        logger.warning(
            "CoinGecko chart request blocked: "
            "coin_id=%s days=%s status_code=429 reason=%s",
            coin_id,
            days,
            error,
        )

        return stale_chart or {
            "prices": [],
        }

    except CoinGeckoChartRequestError as exc:
        if exc.status_code == 429:
            chart_request_cooldown.activate()

        logger.warning(
            "CoinGecko chart request failed: "
            "coin_id=%s days=%s "
            "status_code=%s",
            coin_id,
            days,
            exc.status_code,
        )

        return stale_chart or {
            "prices": [],
        }

    except Exception:
        return stale_chart or {
            "prices": [],
        }

def safe_float(
    value,
) -> float:
    try:
        if value is None:
            return 0.0

        return float(value)

    except Exception:
        return 0.0