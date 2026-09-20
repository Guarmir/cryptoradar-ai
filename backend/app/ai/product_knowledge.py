from dataclasses import dataclass

from app.ai.assistant_intent import (
    normalize_text,
)


PRODUCT_KNOWLEDGE_VERSION = "v1"


@dataclass(frozen=True)
class ProductKnowledgeEntry:
    key: str
    title: str
    keywords: tuple[str, ...]
    content: str


PRODUCT_KNOWLEDGE = (
    ProductKnowledgeEntry(
        key="asset_search",
        title="Pesquisa de ativos",
        keywords=(
            "pesquisa",
            "pesquisar moeda",
            "buscar moeda",
            "buscar ativo",
            "ativo",
            "moeda",
        ),
        content=(
            "O CryptoRadar permite pesquisar "
            "criptomoedas e consultar dados "
            "de mercado e analises disponiveis "
            "para o ativo."
        ),
    ),
    ProductKnowledgeEntry(
        key="score",
        title="Score do ativo",
        keywords=(
            "score",
            "pontuacao",
            "nota",
            "sinal",
        ),
        content=(
            "O score organiza fatores de "
            "mercado em uma leitura resumida. "
            "Ele serve como apoio a analise "
            "e nao representa garantia de "
            "resultado ou ordem automatica "
            "de compra ou venda."
        ),
    ),
    ProductKnowledgeEntry(
        key="position_monitor",
        title="Monitor de posicao",
        keywords=(
            "posicao",
            "posicao aberta",
            "monitor",
            "monitorar",
            "entrada",
        ),
        content=(
            "O monitor de posicao permite "
            "registrar uma posicao que o "
            "usuario deseja acompanhar. "
            "O CryptoRadar usa esse contexto "
            "para organizar o acompanhamento "
            "e os alertas relacionados."
        ),
    ),
    ProductKnowledgeEntry(
        key="notifications",
        title="Notificacoes",
        keywords=(
            "notificacao",
            "notificacoes",
            "alerta",
            "alertas",
            "push",
        ),
        content=(
            "O CryptoRadar possui notificacoes "
            "para eventos monitorados. "
            "A entrega depende do backend, "
            "da conexao do dispositivo e das "
            "permissoes de notificacao do "
            "sistema operacional."
        ),
    ),
    ProductKnowledgeEntry(
        key="market_intelligence",
        title="Inteligencia de mercado",
        keywords=(
            "mercado",
            "oportunidade",
            "oportunidades",
            "inteligencia",
            "radar",
        ),
        content=(
            "A inteligencia de mercado do "
            "CryptoRadar organiza dados, "
            "movimentos e evidencias para "
            "facilitar a interpretacao do "
            "mercado. Ela e uma ferramenta "
            "de apoio a decisao."
        ),
    ),
)


def search_product_knowledge(
    question: str,
    *,
    limit: int = 3,
) -> tuple[
    ProductKnowledgeEntry,
    ...,
]:
    if limit < 1:
        raise ValueError(
            "limit deve ser maior que zero."
        )

    normalized_question = (
        normalize_text(
            question,
        )
    )

    if not normalized_question:
        return ()

    scored_entries = []

    for entry in PRODUCT_KNOWLEDGE:
        score = sum(
            1
            for keyword in entry.keywords
            if normalize_text(
                keyword,
            ) in normalized_question
        )

        if score > 0:
            scored_entries.append(
                (
                    score,
                    entry,
                )
            )

    scored_entries.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return tuple(
        entry
        for _, entry
        in scored_entries[:limit]
    )