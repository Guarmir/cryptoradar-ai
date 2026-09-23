import unicodedata


class RadarAIAssetFocusResolver:
    OVERVIEW = "overview"
    SCORE = "score"
    SIGNAL = "signal"
    RISK = "risk"
    PRICE = "price"
    CHANGE = "change"
    VOLUME = "volume"
    MARKET_CAP = "market_cap"
    INVALIDATION = "invalidation"
    EXPLANATION = "explanation"

    OPERATIONAL_RANGE = "operational_range"
    RANGE_POSITION = "range_position"
    RANGE_SPACE = "range_space"

    _EXPLANATION_TERMS = (
        "por que",
        "porque",
        "motivo",
        "motivos",
        "razao",
        "razoes",
        "explique",
        "explica",
        "explicar",
        "sustenta",
        "sustentando",
        "justifica",
        "justificando",
    )

    _SCORE_TERMS = (
        "score",
        "pontuacao",
        "nota",
    )

    _SIGNAL_TERMS = (
        "sinal",
        "signal",
        "bullish",
        "bearish",
        "tendencia",
    )

    _RISK_TERMS = (
        "risco",
        "riscos",
        "risk",
        "perigo",
    )

    _MARKET_CAP_TERMS = (
        "capitalizacao",
        "market cap",
        "valor de mercado",
    )

    _INVALIDATION_TERMS = (
        "invalidacao",
        "invalida",
        "invalidar",
    )

    _RANGE_POSITION_TERMS = (
        "onde esta",
        "posicao na faixa",
        "posicao dentro",
        "dentro da faixa",
        "regiao da faixa",
        "parte da faixa",
    )

    _RANGE_SPACE_TERMS = (
        "quanto espaco",
        "espaco ate",
        "distancia ate",
        "distancia do limite",
        "ate a resistencia",
        "ate o suporte",
        "limite superior",
        "limite inferior",
    )

    _OPERATIONAL_RANGE_TERMS = (
        "faixa operacional",
        "amplitude operacional",
        "amplitude da faixa",
        "faixa recente",
        "intervalo operacional",
        "faixa",
    )

    _PRICE_TERMS = (
        "preco",
        "price",
        "cotacao",
        "valor",
    )

    _CHANGE_TERMS = (
        "variacao",
        "variou",
        "mudanca",
        "change",
        "24h",
        "alta",
        "queda",
        "subiu",
        "caiu",
    )

    _VOLUME_TERMS = (
        "volume",
        "liquidez",
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
            self._EXPLANATION_TERMS,
        ):
            return self.EXPLANATION

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
            self._MARKET_CAP_TERMS,
        ):
            return self.MARKET_CAP

        if self._contains_any(
            normalized,
            self._INVALIDATION_TERMS,
        ):
            return self.INVALIDATION

        if self._contains_any(
            normalized,
            self._RANGE_POSITION_TERMS,
        ):
            return self.RANGE_POSITION

        if self._contains_any(
            normalized,
            self._RANGE_SPACE_TERMS,
        ):
            return self.RANGE_SPACE

        if self._contains_any(
            normalized,
            self._OPERATIONAL_RANGE_TERMS,
        ):
            return self.OPERATIONAL_RANGE

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