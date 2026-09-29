from app.early_movement.scanner.scanner_ranked_result import (
    EarlyMovementScannerRankedResult,
)
from app.push.push_delivery_models import (
    PushNotificationMessage,
)


class EarlyMovementScannerPushMessageBuilder:
    def build(
        self,
        result: EarlyMovementScannerRankedResult,
    ) -> PushNotificationMessage:
        state = result.state

        state_value = (
            state.value
            if state is not None
            else "unknown"
        )

        title = (
            f"CryptoRadar: {result.symbol.upper()}"
        )

        body = (
            f"{result.name} detectado pelo radar "
            f"de movimento inicial. "
            f"Relevancia: "
            f"{result.relevance_score:.1f}."
        )

        return PushNotificationMessage(
            title=title,
            body=body,
            data={
                "type": "early_movement",
                "coin_id": result.coin_id,
                "symbol": result.symbol,
                "name": result.name,
                "state": state_value,
                "rank": str(result.rank),
                "relevance_score": str(
                    result.relevance_score
                ),
            },
        )