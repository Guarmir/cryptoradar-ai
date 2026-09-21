class RadarAIIntentResolver:
    MARKET_OVERVIEW = "market_overview"
    UNKNOWN = "unknown"

    _MARKET_OVERVIEW_TERMS = (
        "mercado",
        "market",
        "visão geral",
        "visao geral",
        "panorama",
        "cenário",
        "cenario",
        "como está",
        "como esta",
        "como anda",
        "situação do mercado",
        "situacao do mercado",
    )

    def resolve(self, question: str) -> str:
        normalized_question = question.strip().lower()

        if not normalized_question:
            raise ValueError(
                "question must not be empty"
            )

        if any(
            term in normalized_question
            for term in self._MARKET_OVERVIEW_TERMS
        ):
            return self.MARKET_OVERVIEW

        return self.UNKNOWN

    def __call__(self, question: str) -> str:
        return self.resolve(question)