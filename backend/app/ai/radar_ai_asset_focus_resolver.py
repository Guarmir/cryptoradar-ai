import unicodedata


class RadarAIAssetFocusResolver:
    OVERVIEW = "overview"
    SCORE = "score"
    SIGNAL = "signal"
    RISK = "risk"
    PRICE = "price"
    CHANGE = "change"
    VOLUME = "volume"
    INVALIDATION = "invalidation"

    _SCORE_TERMS = (
        "score",
        "pontuacao",
        "pontuação",
        "nota",
    )

    _SIGNAL_TERMS = (
        "sinal",
        "signal",
        "bullish",
        "bearish",
    )

    _RISK_TERMS = (
        "risco",
        "riscos",
        "risk",
        "perigo",
    )

    _PRICE_TERMS = (
        "preco",
        "preço",
        "price",
        "cotacao",
        "cotação",
        "valor",
    )

    _CHANGE_TERMS = (
        "variacao",
        "variação",
        "variou",
        "mudanca",
        "mudança",
        "change",
        "24h",
    )

    _VOLUME_TERMS = (
        "volume",
        "liquidez",
    )

    _INVALIDATION_TERMS = (
        "invalidacao",
        "invalidação",
        "invalida",
        "invalidar",
    )

    def resolve(
        self,
        question: str,
    ) -> str:
        normalized = self._normalize(
            question
        )

        if not normalized:
            raise ValueError(
                "question must not be empty"
            )

        if self._contains_any(
            normalized,
            self._SCORE_TERMS,
        ):
            return self.SCORE

        if self._contains_any(
            normalized,
            self._SIGNAL_TERMS,
        ):
            return self.SIGNAL

        if self._contains_any(
            normalized,
            self._RISK_TERMS,
        ):
            return self.RISK

        if self._contains_any(
            normalized,
            self._PRICE_TERMS,
        ):
            return self.PRICE

        if self._contains_any(
            normalized,
            self._CHANGE_TERMS,
        ):
            return self.CHANGE

        if self._contains_any(
            normalized,
            self._VOLUME_TERMS,
        ):
            return self.VOLUME

        if self._contains_any(
            normalized,
            self._INVALIDATION_TERMS,
        ):
            return self.INVALIDATION

        return self.OVERVIEW

    def __call__(
        self,
        question: str,
    ) -> str:
        return self.resolve(
            question
        )

    @staticmethod
    def _contains_any(
        text: str,
        terms: tuple[str, ...],
    ) -> bool:
        return any(
            RadarAIAssetFocusResolver._normalize(
                term
            )
            in text
            for term in terms
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