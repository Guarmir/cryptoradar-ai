from fastapi import APIRouter, HTTPException

from app.services.asset_analysis_service import (
    build_empty_asset_response,
    calculate_ai_score,
    generate_ai_analysis,
    get_ai_confidence,
    get_ai_signal,
)
from app.services.market_data_service import (
    get_chart_data,
    get_market_data,
    resolve_coin_id,
    safe_float,
)
from app.services.asset_analysis_service import (
    build_empty_asset_response,
    calculate_ai_score,
    calculate_score_from_market,
    generate_ai_analysis,
    get_ai_confidence,
    get_ai_signal,
)


def create_asset_router() -> APIRouter:
    router = APIRouter(
        tags=["assets"],
    )

    @router.get("/analysis/{symbol}")
    def get_analysis(symbol: str):
        coin_id = resolve_coin_id(symbol)

        if not coin_id:
            raise HTTPException(
                status_code=404,
                detail="Ativo não encontrado.",
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

    @router.get("/price/{coin}")
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

    @router.get("/score/{coin}")
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

    @router.get("/chart/{coin}")
    def get_chart(
        coin: str,
        days: int = 1,
    ):
        if days not in [1, 7]:
            raise HTTPException(
                status_code=400,
                detail="Use days=1 ou days=7.",
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

    @router.get("/asset/{coin}")
    def get_asset(
        coin: str,
        days: int = 1,
    ):
        if days not in [1, 7]:
            raise HTTPException(
                status_code=400,
                detail="Use days=1 ou days=7.",
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

    return router