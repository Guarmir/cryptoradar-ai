import re
import unicodedata
from typing import Callable, Optional

from app.services import market_data_service
from app.services.market_data_service import (
    PREFERRED_ALIASES,
)


class RadarAIAssetComparisonResolver:
    MAX_ASSETS = 2

    _COMPARISON_CUES = (
        "compare",
        "comparar",
        "comparacao",
        "versus",
        " vs ",
        " entre ",
        " melhor ",
        " maior ",
        " menor ",
        " ou ",
    )

    _STOPWORDS = frozenset(
        {
            "a",
            "agora",
            "analise",
            "analisar",
            "ativo",
            "ativos",
            "com",
            "como",
            "compare",
            "comparar",
            "comparacao",
            "cotacao",
            "cripto",
            "crypto",
            "da",
            "das",
            "de",
            "do",
            "dos",
            "e",
            "entre",
            "esta",
            "hoje",
            "maior",
            "market",
            "melhor",
            "menor",
            "mercado",
            "o",
            "os",
            "ou",
            "para",
            "preco",
            "qual",
            "quais",
            "risco",
            "riscos",
            "score",
            "sinal",
            "sobre",
            "um",
            "uma",
            "valor",
            "variacao",
            "versus",
            "volume",
            "vs",
        }
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

    def resolve(
        self,
        question: str,
    ) -> tuple[str, ...]:
        normalized_question = self._normalize(
            question
        )

        if not normalized_question:
            raise ValueError(
                "question must not be empty"
            )

        tokens = re.findall(
            r"[a-z0-9-]+",
            normalized_question,
        )

        assets: list[str] = []

        self._append_known_assets(
            tokens,
            assets,
        )

        if len(assets) >= self.MAX_ASSETS:
            return tuple(
                assets[: self.MAX_ASSETS]
            )

        if not self._has_comparison_cue(
            normalized_question
        ):
            return tuple(assets)

        canonical_ids = set(
            PREFERRED_ALIASES.values()
        )

        for token in tokens:
            if len(assets) >= self.MAX_ASSETS:
                break

            if token in self._STOPWORDS:
                continue

            if token in PREFERRED_ALIASES:
                continue

            if token in canonical_ids:
                continue

            if len(token) < 2:
                continue

            resolved = (
                self._dynamic_coin_resolver(
                    token
                )
            )

            if (
                resolved
                and resolved not in assets
            ):
                assets.append(
                    resolved
                )

        return tuple(assets)

    def __call__(
        self,
        question: str,
    ) -> tuple[str, ...]:
        return self.resolve(
            question
        )

    @staticmethod
    def _append_known_assets(
        tokens: list[str],
        assets: list[str],
    ) -> None:
        canonical_ids = set(
            PREFERRED_ALIASES.values()
        )

        for token in tokens:
            asset_id = None

            if token in PREFERRED_ALIASES:
                asset_id = (
                    PREFERRED_ALIASES[
                        token
                    ]
                )
            elif token in canonical_ids:
                asset_id = token

            if (
                asset_id
                and asset_id not in assets
            ):
                assets.append(
                    asset_id
                )

    @classmethod
    def _has_comparison_cue(
        cls,
        question: str,
    ) -> bool:
        padded = f" {question} "

        return any(
            cue in padded
            for cue in cls._COMPARISON_CUES
        )

    @staticmethod
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