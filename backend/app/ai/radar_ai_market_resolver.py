class RadarAIMarketResolver:
    CRYPTO = "crypto"
    UNKNOWN = "unknown"

    _CRYPTO_TERMS = (
        "cripto",
        "crypto",
        "criptomoeda",
        "criptomoedas",
        "bitcoin",
        "btc",
        "ethereum",
        "eth",
        "altcoin",
        "altcoins",
        "token",
        "tokens",
        "mercado cripto",
        "mercado crypto",
    )

    def resolve(self, question: str) -> str:
        normalized_question = question.strip().lower()

        if not normalized_question:
            raise ValueError(
                "question must not be empty"
            )

        if any(
            term in normalized_question
            for term in self._CRYPTO_TERMS
        ):
            return self.CRYPTO

        return self.UNKNOWN

    def __call__(self, question: str) -> str:
        return self.resolve(question)