from app.ai.assistant_context import (
    AssistantContextItem,
)


def build_asset_operational_range_items(
    *,
    name: str,
    assessment,
    recurrence_assessment=None,
    quality_assessment=None,
    invalidation_assessment=None,
    consolidated_context=None,
) -> tuple[
    AssistantContextItem,
    ...,
]:
    if assessment is None:
        return (
            AssistantContextItem(
                key=(
                    "asset_operational_range"
                ),
                title="Faixa operacional",
                content=(
                    "Não há histórico "
                    "suficiente para calcular "
                    "a faixa operacional "
                    f"recente de {name}."
                ),
            ),
        )

    amplitude_status = (
        "está dentro"
        if (
            assessment
            .is_operational_amplitude
        )
        else "está fora"
    )

    range_content = (
        f"A faixa recente observada "
        f"de {name} vai de "
        f"US$ "
        f"{assessment.lower_limit:,.8f} "
        f"até US$ "
        f"{assessment.upper_limit:,.8f}. "
        f"A amplitude é de "
        f"{assessment.amplitude_percent:.2f}% "
        f"e {amplitude_status} da "
        f"faixa-alvo operacional "
        f"de 4% a 6%."
    )

    if recurrence_assessment is not None:
        range_content = (
            f"{range_content} "
            f"{build_asset_operational_range_recurrence_text(recurrence_assessment)}"
        )

    items = [
        AssistantContextItem(
            key=(
                "asset_operational_range"
            ),
            title="Faixa operacional",
            content=range_content,
        ),
        AssistantContextItem(
            key=(
                "asset_operational_range_position"
            ),
            title="Posição na faixa",
            content=(
                f"A posição relativa do preço "
                f"de {name} é "
                f"{assessment.position_percent:.2f}% "
                f"da amplitude observada "
                f"(0% = limite inferior; "
                f"100% = limite superior)."
            ),
        ),
        AssistantContextItem(
            key=(
                "asset_operational_range_space"
            ),
            title="Espaço na faixa",
            content=(
                f"Distância do preço atual "
                f"ao limite inferior: "
                f"{assessment.distance_to_lower_percent:.2f}%. "
                f"Distância ao limite superior: "
                f"{assessment.distance_to_upper_percent:.2f}%."
            ),
        ),
    ]

    if quality_assessment is not None:
        items.append(
            AssistantContextItem(
                key=(
                    "asset_operational_range_quality"
                ),
                title=(
                    "Qualidade da faixa"
                ),
                content=(
                    build_asset_operational_range_quality_text(
                        name=name,
                        assessment=(
                            quality_assessment
                        ),
                    )
                ),
            )
        )

    if invalidation_assessment is not None:
        items.append(
            AssistantContextItem(
                key=(
                    "asset_operational_range_invalidation"
                ),
                title=(
                    "Risco de invalidação "
                    "da faixa"
                ),
                content=(
                    build_asset_operational_range_invalidation_text(
                        name=name,
                        assessment=(
                            invalidation_assessment
                        ),
                    )
                ),
            )
        )

    if consolidated_context is not None:
        items.append(
            AssistantContextItem(
                key=(
                    "asset_operational_range_context"
                ),
                title=(
                    "Contexto operacional "
                    "consolidado"
                ),
                content=(
                    build_asset_operational_range_context_text(
                        name=name,
                        assessment=(
                            consolidated_context
                        ),
                    )
                ),
            )
        )

    return tuple(items)


def build_asset_operational_range_recurrence_text(
    assessment,
) -> str:
    details = (
        f"Foram identificados "
        f"{assessment.lower_limit_touches} "
        f"toques no limite inferior e "
        f"{assessment.upper_limit_touches} "
        f"toques no limite superior, "
        f"com "
        f"{assessment.completed_oscillations} "
        f"oscilações completas estimadas."
    )

    if (
        assessment
        .suggests_organized_oscillation
    ):
        return (
            f"{details} "
            f"A recorrência é forte e "
            f"equilibrada, sugerindo "
            f"oscilação organizada "
            f"dentro da faixa observada."
        )

    if (
        assessment
        .suggests_recurring_range
    ):
        return (
            f"{details} "
            f"A faixa apresenta "
            f"recorrência mínima "
            f"confirmada, mas o histórico "
            f"ainda não é forte o "
            f"suficiente para classificá-la "
            f"como oscilação organizada."
        )

    return (
        f"{details} "
        f"A recorrência observada ainda "
        f"é insuficiente para confirmar "
        f"comportamento repetitivo "
        f"entre os dois limites."
    )


def build_asset_operational_range_quality_text(
    *,
    name: str,
    assessment,
) -> str:
    labels = {
        "strong": "forte",
        "acceptable": "aceitável",
        "under_observation": (
            "em observação"
        ),
        "weak": "fraca",
    }

    label = labels.get(
        assessment.state,
        assessment.state,
    )

    return (
        f"A qualidade operacional "
        f"da faixa de {name} é "
        f"{label}. "
        f"Confirmação por volume: "
        f"{assessment.volume_confirmation_state}. "
        f"Liquidez observada: "
        f"{assessment.liquidity_state}."
    )


def build_asset_operational_range_invalidation_text(
    *,
    name: str,
    assessment,
) -> str:
    labels = {
        "low": "baixo",
        "moderate": "moderado",
        "high": "alto",
        "invalidated": "invalidada",
    }

    label = labels.get(
        assessment.state,
        assessment.state,
    )

    if assessment.is_invalidated:
        return (
            f"A faixa observada de {name} "
            f"está invalidada porque o "
            f"preço atual saiu dos limites "
            f"utilizados no cálculo."
        )

    return (
        f"O risco estrutural observado "
        f"de invalidação da faixa de "
        f"{name} é {label}. "
        f"Esse indicador descreve a "
        f"estrutura da faixa e não o "
        f"risco total do ativo."
    )


def build_asset_operational_range_context_text(
    *,
    name: str,
    assessment,
) -> str:
    labels = {
        "organized": (
            "organizado"
        ),
        "usable": (
            "utilizável, mas sem "
            "confirmação forte"
        ),
        "under_observation": (
            "em observação"
        ),
        "invalidated": (
            "invalidado"
        ),
    }

    zones = {
        "below_range": (
            "abaixo da faixa"
        ),
        "lower": (
            "região inferior"
        ),
        "middle": (
            "região central"
        ),
        "upper": (
            "região superior"
        ),
        "above_range": (
            "acima da faixa"
        ),
    }

    state_label = labels.get(
        assessment.state,
        assessment.state,
    )

    zone_label = zones.get(
        assessment.position_zone,
        assessment.position_zone,
    )

    return (
        f"O contexto operacional "
        f"consolidado de {name} está "
        f"{state_label}. "
        f"O preço está na "
        f"{zone_label}. "
        f"Essa leitura é observacional "
        f"e não representa recomendação "
        f"de compra ou venda."
    )