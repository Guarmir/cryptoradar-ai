
from collections.abc import Iterable
from typing import TypeVar

from app.early_movement.scanner.scanner_candidate_rotation import (
    EarlyMovementScannerCandidateRotation,
)


CandidateT = TypeVar("CandidateT")


class EarlyMovementScannerRotationBridge:
    """
    Integra a rotação ao scanner e recebe
    confirmações do carregador de gráficos.

    Falhas internas da rotação não devem
    interromper a análise de mercado.
    """

    def __init__(
        self,
        *,
        acquisition_budget: int = 4,
        priority_slots: int = 1,
    ) -> None:
        if acquisition_budget < 1:
            raise ValueError(
                "O orçamento deve ser maior que zero."
            )

        self._acquisition_budget = acquisition_budget
        self._rotation = (
            EarlyMovementScannerCandidateRotation(
                priority_slots=priority_slots,
            )
        )

    def arrange(
        self,
        candidates: Iterable[CandidateT],
    ) -> tuple[CandidateT, ...]:
        original = tuple(candidates)

        try:
            arranged = self._rotation.arrange(
                original,
                acquisition_budget=(
                    self._acquisition_budget
                ),
            )
        except Exception:
            return original

        return arranged

    def on_chart_result(
        self,
        coin_id: str,
        success: bool,
    ) -> None:
        try:
            if success:
                self._rotation.record_success(
                    coin_id,
                )
            else:
                self._rotation.record_failure(
                    coin_id,
                )
        except Exception:
            # A rotação é auxiliar.
            # Uma falha nela não pode impedir
            # a análise do gráfico.
            return
