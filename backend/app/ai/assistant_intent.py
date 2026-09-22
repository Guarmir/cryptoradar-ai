import unicodedata
from enum import Enum


class AssistantIntent(
    str,
    Enum,
):
    PRODUCT_HELP = "product_help"
    MARKET_OVERVIEW = "market_overview"
    ASSET_ANALYSIS = "asset_analysis"
    UNKNOWN = "unknown"


_MARKET_OVERVIEW_PHRASES = (
    "como esta o mercado",
    "mercado hoje",
    "resumo do mercado",
    "visao do mercado",
    "cenario do mercado",
    "sentimento do mercado",
    "movimento do mercado",
    "oportunidades hoje",
    "oportunidades do mercado",
    "ativos em alta",
    "ativos em queda",
    "o que esta acontecendo no mercado",
    "o que esta chamando atencao",
)


_PRODUCT_HELP_PHRASES = (
    "como usar",
    "como configuro",
    "como configurar",
    "como funciona",
    "o que significa",
    "para que serve",
    "funcionalidade",
    "funcao",
    "score",
    "alerta",
    "notificacao",
    "monitor",
    "posicao aberta",
    "plano free",
    "plano pro",
    "cryptoradar",
)


def classify_assistant_intent(
    question: str,
) -> AssistantIntent:
    normalized = _normalize(
        question,
    )

    if not normalized:
        return AssistantIntent.UNKNOWN

    if _contains_any(
        normalized,
        _MARKET_OVERVIEW_PHRASES,
    ):
        return (
            AssistantIntent
            .MARKET_OVERVIEW
        )

    if _contains_any(
        normalized,
        _PRODUCT_HELP_PHRASES,
    ):
        return (
            AssistantIntent
            .PRODUCT_HELP
        )

    return AssistantIntent.UNKNOWN


def _contains_any(
    text: str,
    phrases: tuple[str, ...],
) -> bool:
    return any(
        phrase in text
        for phrase in phrases
    )


def normalize_text(
    value: str,
) -> str:
    return _normalize(
        value,
    )


def _normalize(
    value: str,
) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        value.strip().lower(),
    )

    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(
            character
        )
    )