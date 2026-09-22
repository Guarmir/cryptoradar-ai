import re
import unicodedata
from typing import Callable, Optional

from app.services import market_data_service
from app.services.market_data_service import (
    PREFERRED_ALIASES,
)


class RadarAIAssetResolver:
    _STOPWORDS = frozenset(
        {
            "a",
            "agora",
            "analise",
            "analisar",
            "ativo",
            "ativos",
            "bearish",
            "bullish",
            "cenario",
            "como",
            "com",
            "cotacao",
            "cripto",
            "crypto",
            "criptomoeda",
            "criptomoedas",
            "da",
            "das",
            "de",
            "do",
            "dos",
            "esta",
            "esse",
            "essa",
            "geral",
            "gerais",
            "hoje",
            "informacoes",
            "market",
            "mercado",
            "me",
            "movimento",
            "o",
            "oportunidades",
            "os",
            "panorama",
            "para",
            "preco",
            "qual",
            "quais",
            "risco",
            "riscos",
            "score",
            "sentimento",
            "sinal",
            "situacao",
            "sobre",
            "tendencia",
            "um",
            "uma",
            "valor",
            "variacao",
            "variou",
            "visao",
            "volume",
        }
    )

    _DYNAMIC_ASSET_CUES = (
        "analise",
        "analisar",
        "como esta",
        "preco",
        "cotacao",
        "valor",
        "score",
        "sinal",
        "risco",
        "riscos",
        "variacao",
        "variou",
        "volume",
        "bullish",
        "bearish",
        "tendencia",
        "o que esta acontecendo com",
    )

    def __init__(
        self,
        *,
        dynamic_coin_resolver: Optional[
            Callable[[str], Optional[str]]
        ] = None,
    ) -> None:
        self._dynamic_coin_resolver = (
            dynamic_coin_resolver
            or market_data_service.resolve_coin_id
        )

        self._question_cache: dict[
            str,
            Optional[str],
        ] = {}

    def resolve(
        self,
        question: str,
    ) -> Optional[str]:
        normalized_question = (
            self._normalize(
                question
            )
        )

        if not normalized_question:
            raise ValueError(
                "question must not be empty"
            )

        if (
            normalized_question
            in self._question_cache
        ):
            return self._question_cache[
                normalized_question
            ]

        tokens = re.findall(
            r"[a-z0-9-]+",
            normalized_question,
        )

        known_asset = (
            self._resolve_known_asset(
                tokens
            )
        )

        if known_asset is not None:
            self._question_cache[
                normalized_question
            ] = known_asset

            return known_asset

        if not self._has_dynamic_asset_cue(
            normalized_question
        ):
            self._question_cache[
                normalized_question
            ] = None

            return None

        candidates = [
            token
            for token in tokens
            if (
                token not in self._STOPWORDS
                and len(token) >= 2
            )
        ]

        for candidate in reversed(
            candidates
        ):
            resolved = (
                self._dynamic_coin_resolver(
                    candidate
                )
            )

            if resolved:
                self._question_cache[
                    normalized_question
                ] = resolved

                return resolved

        self._question_cache[
            normalized_question
        ] = None

        return None

    def __call__(
        self,
        question: str,
    ) -> Optional[str]:
        return self.resolve(
            question
        )

    @classmethod
    def _has_dynamic_asset_cue(
        cls,
        question: str,
    ) -> bool:
        return any(
            cue in question
            for cue in cls._DYNAMIC_ASSET_CUES
        )

    @staticmethod
    def _resolve_known_asset(
        tokens: list[str],
    ) -> Optional[str]:
        for token in tokens:
            if token in PREFERRED_ALIASES:
                return PREFERRED_ALIASES[
                    token
                ]

        canonical_ids = set(
            PREFERRED_ALIASES.values()
        )

        for token in tokens:
            if token in canonical_ids:
                return token

        return None

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        normalized = (
            unicodedata.normalize(
                "NFKD",
                value.strip().lower(),
            )
        )

        return "".join(
            character
            for character in normalized
            if not unicodedata.combining(
                character
            )
        )