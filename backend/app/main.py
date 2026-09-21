from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import threading
import time

from app.access.access_api import (
    AccessEntitlementsResponse,
    get_access_entitlements,
)
from app.ai.radar_ai_router import (
    create_radar_ai_router,
)
from app.monitoring.monitoring_fastapi_lifecycle import (
    monitoring_lifespan,
)
from app.push.push_registration_api import (
    PushDeviceRegistrationRequest,
    PushDeviceRegistrationResponse,
    register_push_device,
)
from app.services.asset_analysis_service import (
    build_empty_asset_response,
    calculate_ai_score,
    calculate_score_from_market,
    generate_ai_analysis,
    get_ai_confidence,
    get_ai_signal,
)
from app.services.price_alert import monitor_price

app = FastAPI(
    title="CryptoRadar AI",
    version="2.1.0",
    lifespan=monitoring_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    create_radar_ai_router()
)

COINGECKO_API = "https://api.coingecko.com/api/v3"

coin_list_cache = {
    "data": None,
    "timestamp": 0
}

market_cache = {}
chart_cache = {}

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


def get_cached(cache_dict, key, ttl):
    item = cache_dict.get(key)

    if not item:
        return None

    if time.time() - item["timestamp"] > ttl:
        return None

    return item["data"]


def set_cached(cache_dict, key, data):
    cache_dict[key] = {
        "data": data,
        "timestamp": time.time()
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
                    "Erro ao buscar lista de moedas."
                ),
            )

        data = response.json()

        coin_list_cache["data"] = data
        coin_list_cache["timestamp"] = (
            time.time()
        )

        return data

    except Exception:
        raise HTTPException(
            status_code=503,
            detail=(
                "Erro ao buscar lista de moedas."
            ),
        )


def resolve_coin_id(user_input: str):
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
            return exact_symbol_matches[0][
                "id"
            ]

        preferred_names = {
            "btc": "bitcoin",
            "eth": "ethereum",
            "sol": "solana",
            "xrp": "ripple",
            "ada": "cardano",
            "doge": "dogecoin",
        }

        preferred_name = (
            preferred_names.get(
                query
            )
        )

        if preferred_name:
            for coin in (
                exact_symbol_matches
            ):
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


def get_market_data(coin_id: str):
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
        "price_change_percentage": "24h"
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
                "prices": []
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
            "prices": []
        }


def safe_float(value):
    try:
        if value is None:
            return 0.0

        return float(value)

    except Exception:
        return 0.0


@app.get("/analysis/{symbol}")
def get_analysis(symbol: str):
    coin_id = resolve_coin_id(symbol)

    if not coin_id:
        raise HTTPException(
            status_code=404,
            detail=(
                "Ativo não encontrado."
            ),
        )

    market = get_market_data(
        coin_id
    )

    if not market:
        raise HTTPException(
            status_code=503,
            detail=(
                "Dados de mercado "
                "indisponíveis."
            ),
        )

    price = safe_float(
        market.get("current_price")
    )

    market_cap = safe_float(
        market.get("market_cap")
    )

    volume = safe_float(
        market.get("total_volume")
    )

    change_24h = safe_float(
        market.get(
            "price_change_percentage_24h"
        )
    )

    score = calculate_ai_score(
        change_24h,
        volume,
        market_cap,
    )

    signal = get_ai_signal(
        score
    )

    confidence = get_ai_confidence(
        score,
        market_cap,
        volume,
    )

    (
        summary,
        reasons,
        risks,
        invalidation,
    ) = generate_ai_analysis(
        score,
        change_24h,
        volume,
        market_cap,
    )

    return {
        "symbol": (
            market.get(
                "symbol",
                symbol,
            ).upper()
        ),
        "name": market.get(
            "name",
            coin_id,
        ),
        "coin_id": coin_id,
        "price": price,
        "market_cap": market_cap,
        "volume": volume,
        "change_24h": change_24h,
        "score": score,
        "signal": signal,
        "confidence": confidence,
        "summary": summary,
        "reasons": reasons,
        "risks": risks,
        "invalidation": invalidation,
        "image": market.get("image"),
        "last_updated": market.get(
            "last_updated"
        ),
    }


@app.get(
    "/access/entitlements/{installation_id}",
    response_model=(
        AccessEntitlementsResponse
    ),
)
def get_access_entitlements_endpoint(
    installation_id: str,
):
    return get_access_entitlements(
        installation_id,
    )


@app.post(
    "/push/devices/register",
    response_model=(
        PushDeviceRegistrationResponse
    ),
)
def register_push_device_endpoint(
    request: PushDeviceRegistrationRequest,
):
    return register_push_device(
        request,
    )


@app.get("/")
def home():
    return {
        "status": "CryptoRadar AI online",
        "version": "2.1.0",
    }


@app.get("/price/{coin}")
def get_price(coin: str):
    coin_id = resolve_coin_id(
        coin
    )

    if not coin_id:
        return {
            "error": (
                "Moeda não encontrada"
            ),
            "coin": coin.upper(),
            "coin_id": None,
            "price_usd": None,
        }

    market = get_market_data(
        coin_id
    )

    if not market:
        return {
            "error": (
                "Preço indisponível "
                "no momento"
            ),
            "coin": coin.upper(),
            "coin_id": coin_id,
            "price_usd": None,
        }

    return {
        "coin": market.get(
            "symbol",
            coin,
        ).upper(),
        "coin_id": market.get("id"),
        "name": market.get("name"),
        "price_usd": market.get(
            "current_price"
        ),
    }


@app.get(
    "/alert/{coin}/{price}"
)
def start_alert(
    coin: str,
    price: float,
):
    coin_id = resolve_coin_id(
        coin
    )

    if not coin_id:
        return {
            "error": (
                "Moeda não encontrada"
            )
        }

    thread = threading.Thread(
        target=monitor_price,
        args=(
            coin_id,
            price,
        ),
        daemon=True,
    )

    thread.start()

    return {
        "status": "Alerta iniciado",
        "coin": coin.upper(),
        "coin_id": coin_id,
        "target_price": price,
    }


@app.get("/score/{coin}")
def get_score(coin: str):
    coin_id = resolve_coin_id(
        coin
    )

    if not coin_id:
        return {
            "error": (
                "Moeda não encontrada"
            ),
            **build_empty_asset_response(
                coin
            ),
        }

    market = get_market_data(
        coin_id
    )

    if not market:
        return {
            "error": (
                "Dados indisponíveis "
                "no momento. "
                "Tente novamente "
                "em instantes."
            ),
            **build_empty_asset_response(
                coin
            ),
        }

    score, signal = (
        calculate_score_from_market(
            market
        )
    )

    return {
        "coin": market.get(
            "symbol",
            coin,
        ).upper(),
        "coin_id": market.get("id"),
        "name": market.get("name"),
        "score": score,
        "signal": signal,
        "price": market.get(
            "current_price"
        ),
        "market_cap": market.get(
            "market_cap"
        ),
        "volume": market.get(
            "total_volume"
        ),
        "change_24h": market.get(
            "price_change_percentage_24h"
        ),
        "image": market.get("image"),
        "last_updated": market.get(
            "last_updated"
        ),
    }


@app.get("/chart/{coin}")
def get_chart(
    coin: str,
    days: int = 1,
):
    if days not in [1, 7]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Use days=1 ou days=7."
            ),
        )

    coin_id = resolve_coin_id(
        coin
    )

    if not coin_id:
        return {
            "coin": coin.upper(),
            "coin_id": None,
            "days": days,
            "points": [],
        }

    chart_data = get_chart_data(
        coin_id,
        days,
    )

    prices = chart_data.get(
        "prices",
        [],
    )

    points = []

    for item in prices:
        if (
            isinstance(item, list)
            and len(item) >= 2
        ):
            points.append(
                {
                    "timestamp": item[0],
                    "price": item[1],
                }
            )

    return {
        "coin": coin.upper(),
        "coin_id": coin_id,
        "days": days,
        "points": points,
    }


@app.get("/asset/{coin}")
def get_asset(
    coin: str,
    days: int = 1,
):
    if days not in [1, 7]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Use days=1 ou days=7."
            ),
        )

    coin_id = resolve_coin_id(
        coin
    )

    if not coin_id:
        return {
            "error": (
                "Moeda não encontrada"
            ),
            **build_empty_asset_response(
                coin,
                days,
            ),
        }

    market = get_market_data(
        coin_id
    )

    chart_data = get_chart_data(
        coin_id,
        days,
    )

    if not market:
        return {
            "error": (
                "Dados indisponíveis "
                "no momento. "
                "Tente novamente "
                "em instantes."
            ),
            **build_empty_asset_response(
                coin,
                days,
            ),
        }

    score, signal = (
        calculate_score_from_market(
            market
        )
    )

    prices = chart_data.get(
        "prices",
        [],
    )

    points = []

    for item in prices:
        if (
            isinstance(item, list)
            and len(item) >= 2
        ):
            points.append(
                {
                    "timestamp": item[0],
                    "price": item[1],
                }
            )

    return {
        "coin": market.get(
            "symbol",
            coin,
        ).upper(),
        "coin_id": market.get("id"),
        "name": market.get("name"),
        "score": score,
        "signal": signal,
        "price": market.get(
            "current_price"
        ),
        "market_cap": market.get(
            "market_cap"
        ),
        "volume": market.get(
            "total_volume"
        ),
        "change_24h": market.get(
            "price_change_percentage_24h"
        ),
        "image": market.get("image"),
        "last_updated": market.get(
            "last_updated"
        ),
        "days": days,
        "points": points,
    }