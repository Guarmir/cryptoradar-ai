
from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner.scanner_ranked_result import (
    EarlyMovementScannerRankedResult,
)
from app.push.push_delivery_models import (
    PushNotificationMessage,
)


class EarlyMovementScannerPushMessageBuilder:
    @staticmethod
    def _state_description(
        state: EarlyMovementState | None,
    ) -> str:
        descriptions = {
            EarlyMovementState.OBSERVATION:
                "Observacao antecipada - movimento ainda nao confirmado",
            EarlyMovementState.EARLY_MOVEMENT:
                "Movimento inicial identificado",
            EarlyMovementState.CONFIRMED_MOVEMENT:
                "Movimento com confirmacoes adicionais",
        }

        return descriptions.get(
            state,
            "Movimento em acompanhamento",
        )

    
    @staticmethod
    def _direction_description(
        result: EarlyMovementScannerRankedResult,
    ) -> str:
        scanner_result = getattr(
            result,
            "result",
            None,
        )

        if scanner_result is None:
            return "Direcao nao confirmada"

        analysis = getattr(
            scanner_result,
            "analysis",
            None,
        )

        if analysis is None:
            return "Direcao nao confirmada"

        evidence = getattr(
            analysis,
            "evidence",
            None,
        )

        if evidence is None:
            return "Direcao nao confirmada"

        if (
            evidence.support_break
            and not evidence.resistance_break
        ):
            return "Rompimento de suporte"

        if (
            evidence.resistance_break
            and not evidence.support_break
        ):
            return "Rompimento de resistencia"

        return "Direcao nao confirmada"


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

        title = f"CryptoRadar: {result.symbol.upper()}"

        state_description = self._state_description(state)
        direction_description = self._direction_description(result)

        body = (
            f"{result.name}: "
            f"{state_description}. "
            f"{direction_description}. "
            f"Relevancia: {result.relevance_score:.1f}."
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
