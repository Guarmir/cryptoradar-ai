import threading

from fastapi import APIRouter

from app.services.market_data_service import (
    resolve_coin_id,
)
from app.services.price_alert import (
    monitor_price,
)


def create_alert_router() -> APIRouter:
    router = APIRouter(
        tags=["alerts"],
    )

    @router.get(
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

    return router