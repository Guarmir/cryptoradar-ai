from app.monitoring.market_event import MarketEvent
from app.push.push_delivery_models import (
    PushNotificationMessage,
)


class MarketEventPushMessageBuilder:
    def build(
        self,
        event: MarketEvent,
    ) -> PushNotificationMessage:
        change = abs(
            event.price_change_percent
        )

        if event.is_upward:
            direction = "alta"
        else:
            direction = "queda"

        title = (
            f"{event.symbol}: movimento de "
            f"{direction}"
        )

        body = (
            f"O preço variou {change:.2f}% "
             "desde a última observação."
        )

        return PushNotificationMessage(
            title=title,
            body=body,
            data={
                "type": "market_event",
                "event_type": event.event_type,
                "symbol": event.symbol,
                "previous_price": (
                    str(event.previous_price)
                ),
                "current_price": (
                    str(event.current_price)
                ),
                "price_change_percent": (
                    str(event.price_change_percent)
                ),
                "observed_at": (
                    event.observed_at.isoformat()
                ),
            },
        )