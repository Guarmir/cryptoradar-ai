from typing import Any


class RadarAIAnswerComposer:
    def compose(
        self,
        context: Any,
    ) -> str:
        if not context.is_supported:
            return (
                "Ainda não tenho contexto "
                "suficiente para responder "
                "essa pergunta."
            )

        contents = [
            item.content.strip()
            for item in context.items
            if item.content.strip()
        ]

        if not contents:
            return (
                "Os dados foram processados, "
                "mas não há informações "
                "suficientes para montar "
                "uma resposta."
            )

        return "\n\n".join(
            contents
        )

    def __call__(
        self,
        context: Any,
    ) -> str:
        return self.compose(
            context
        )