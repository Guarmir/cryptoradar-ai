
import pytest

from app.early_movement.early_movement_direction import (
    EarlyMovementDirection,
)
from app.early_movement.early_movement_direction_classifier import (
    EarlyMovementDirectionClassifier,
)
from app.early_movement.early_movement_metrics import (
    EarlyMovementMetrics,
)
from app.early_movement.early_movement_price_structure import (
    EarlyMovementPriceStructure,
)


@pytest.mark.parametrize(
    (
        "recent_return",
        "acceleration",
        "persistence",
        "volume_ratio",
        "support_break",
        "resistance_break",
        "expected",
    ),
    [
        # Alta com rompimento de resistencia.
        (2.0, 1.0, None, None, False, True, "up"),

        # Baixa com rompimento de suporte.
        (-2.0, -1.0, None, None, True, False, "down"),

        # Alta antecipada, ainda sem rompimento.
        (1.5, 0.8, 65.0, 1.8, False, False, "up"),

        # Baixa antecipada, ainda sem rompimento.
        (-1.5, -0.8, 65.0, 1.8, False, False, "down"),

        # Alta sem evidencias suficientes.
        (1.5, 0.8, 20.0, 1.0, False, False, "neutral"),

        # Baixa sem evidencias suficientes.
        (-1.5, -0.8, 20.0, 1.0, False, False, "neutral"),

        # Queda desacelerando nao confirma alta.
        (-1.0, 0.8, 65.0, 1.8, False, False, "neutral"),

        # Alta desacelerando nao confirma baixa.
        (1.0, -0.8, 65.0, 1.8, False, False, "neutral"),

        # Rompimento contraditorio.
        (2.0, 1.0, 65.0, 1.8, True, False, "neutral"),

        # Dois rompimentos simultaneos.
        (2.0, 1.0, 65.0, 1.8, True, True, "neutral"),

        # Retorno recente insuficiente.
        (None, 1.0, 65.0, 1.8, False, True, "neutral"),

        # Aceleracao insuficiente.
        (2.0, None, 65.0, 1.8, False, True, "neutral"),

        # Movimento pequeno.
        (0.2, 0.1, 65.0, 1.8, False, False, "neutral"),

        # Volume insuficiente antes do rompimento.
        (1.5, 0.8, 65.0, 1.1, False, False, "neutral"),

        # Persistencia insuficiente antes do rompimento.
        (1.5, 0.8, 20.0, 1.8, False, False, "neutral"),
    ],
)
def test_direction_classification(
    recent_return,
    acceleration,
    persistence,
    volume_ratio,
    support_break,
    resistance_break,
    expected,
):
    classifier = EarlyMovementDirectionClassifier()

    result = classifier.classify(
        metrics=EarlyMovementMetrics(
            recent_price_return=recent_return,
            price_acceleration=acceleration,
            persistence_score=persistence,
            abnormal_volume_ratio=volume_ratio,
        ),
        price_structure=EarlyMovementPriceStructure(
            support_break=support_break,
            resistance_break=resistance_break,
        ),
    )

    assert result == EarlyMovementDirection(expected)
