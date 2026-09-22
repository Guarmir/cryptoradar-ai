import re
from typing import Optional

from app.services.market_data_service import (
    PREFERRED_ALIASES,
)


class RadarAIAssetResolver:
    def resolve(
        self,
        question: str,
    ) -> Optional[str]:
        normalized_question = (
            question.strip().lower()
        )

        if not normalized_question:
            raise ValueError(
                "question must not be empty"
            )

        tokens = re.findall(
            r"[a-z0-9-]+",
            normalized_question,
        )

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

    def __call__(
        self,
        question: str,
    ) -> Optional[str]:
        return self.resolve(
            question
        )