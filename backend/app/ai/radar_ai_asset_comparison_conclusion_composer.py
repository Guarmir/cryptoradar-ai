import math
import re
import unicodedata
from typing import Any, Optional


class RadarAIAssetComparisonConclusionComposer:
    SCORE = "score"
    PRICE = "price"
    CHANGE = "change"
    VOLUME = "volume"
    MARKET_CAP = "market_cap"
    RISK = "risk"

    _HIGHER_TERMS = (
        "maior",
        "mais alto",
        "mais alta",
        "melhor",
        "subiu mais",
    )

    _LOWER_TERMS = (
        "menor",
        "mais baixo",
        "mais baixa",
    )

    _SUPPORTED_NUMERIC_FOCUS = frozenset(
        {
            SCORE,
            PRICE,
            CHANGE,
            VOLUME,
            MARKET_CAP,
        }
    )

    def compose(
        self,
        *,
        context: Any,
        question: str,
        focus: str,
    ) -> Optional[str]:
        normalized_question = self._normalize(
            question
        )

        direction = self._resolve_direction(
            normalized_question,
            focus,
        )

        if direction is None:
            return None

        if focus == self.RISK:
            return (
                "Os riscos dos dois ativos podem "
                "ser comparados qualitativamente, "
                "mas o contexto atual ainda não "
                "possui uma métrica numérica de "
                "risco para indicar qual deles "
                "apresenta menor risco."
            )

        if (
            focus
            not in self._SUPPORTED_NUMERIC_FOCUS
        ):
            return None

        first = self._read_asset_metric(
            context=context,
            position=1,
            focus=focus,
        )

        second = self._read_asset_metric(
            context=context,
            position=2,
            focus=focus,
        )

        if (
            first is None
            or second is None
        ):
            return None

        first_name, first_value = first
        second_name, second_value = second

        if math.isclose(
            first_value,
            second_value,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            return (
                f"{first_name} e {second_name} "
                f"estão empatados em "
                f"{self._metric_label(focus)}."
            )

        if direction == "higher":
            winner = (
                first
                if first_value > second_value
                else second
            )

        else:
            winner = (
                first
                if first_value < second_value
                else second
            )

        winner_name = winner[0]

        difference = abs(
            first_value
            - second_value
        )

        comparison_word = (
            "maior"
            if direction == "higher"
            else "menor"
        )

        return (
            f"{winner_name} apresenta "
            f"{comparison_word} "
            f"{self._metric_label(focus)} "
            f"entre os dois ativos. "
            f"Diferença: "
            f"{self._format_difference(
                focus,
                difference,
            )}"
        )

    def __call__(
        self,
        *,
        context: Any,
        question: str,
        focus: str,
    ) -> Optional[str]:
        return self.compose(
            context=context,
            question=question,
            focus=focus,
        )

    @classmethod
    def _resolve_direction(
        cls,
        question: str,
        focus: str,
    ) -> Optional[str]:
        if (
            focus == cls.CHANGE
            and (
                "maior queda" in question
                or "caiu mais" in question
            )
        ):
            return "lower"

        if any(
            term in question
            for term in cls._LOWER_TERMS
        ):
            return "lower"

        if any(
            term in question
            for term in cls._HIGHER_TERMS
        ):
            return "higher"

        return None

    @classmethod
    def _read_asset_metric(
        cls,
        *,
        context: Any,
        position: int,
        focus: str,
    ) -> Optional[
        tuple[str, float]
    ]:
        prefix = (
            f"comparison_asset_{position}"
        )

        items = {
            item.key: item.content.strip()
            for item in context.items
            if item.content.strip()
        }

        identity = items.get(
            f"{prefix}_identity"
        )

        content = items.get(
            f"{prefix}_{focus}"
        )

        if (
            not identity
            or not content
        ):
            return None

        value = cls._extract_value(
            content,
            focus,
        )

        if value is None:
            return None

        return (
            identity,
            value,
        )

    @classmethod
    def _extract_value(
        cls,
        content: str,
        focus: str,
    ) -> Optional[float]:
        if focus == cls.SCORE:
            match = re.search(
                r"score\s+"
                r"(-?\d+(?:[.,]\d+)?)"
                r"/100",
                content,
                flags=re.IGNORECASE,
            )

        elif focus == cls.CHANGE:
            match = re.search(
                r"([+-]?\d+(?:[.,]\d+)?)%",
                content,
            )

        else:
            match = re.search(
                r"US\$\s*"
                r"([0-9][0-9,]*(?:\.\d+)?)",
                content,
                flags=re.IGNORECASE,
            )

        if match is None:
            return None

        raw_value = (
            match.group(1)
            .replace(",", "")
        )

        try:
            return float(raw_value)

        except ValueError:
            return None

    @classmethod
    def _metric_label(
        cls,
        focus: str,
    ) -> str:
        labels = {
            cls.SCORE: "score",
            cls.PRICE: "preço",
            cls.CHANGE: (
                "variação em 24h"
            ),
            cls.VOLUME: (
                "volume em 24h"
            ),
            cls.MARKET_CAP: (
                "capitalização"
            ),
        }

        return labels.get(
            focus,
            focus,
        )

    @classmethod
    def _format_difference(
        cls,
        focus: str,
        difference: float,
    ) -> str:
        if focus == cls.SCORE:
            if difference.is_integer():
                return (
                    f"{int(difference)} pontos."
                )

            return (
                f"{difference:.2f} pontos."
            )

        if focus == cls.CHANGE:
            return (
                f"{difference:.2f} "
                "pontos percentuais."
            )

        if focus == cls.PRICE:
            return (
                f"US$ {difference:,.8f}."
            )

        return (
            f"US$ {difference:,.0f}."
        )

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