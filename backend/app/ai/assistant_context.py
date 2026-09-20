from dataclasses import dataclass
from typing import Optional

from app.ai.assistant_intent import (
    AssistantIntent,
)


@dataclass(frozen=True)
class AssistantContextItem:
    key: str
    title: str
    content: str


@dataclass(frozen=True)
class AssistantContext:
    intent: AssistantIntent
    source: str
    source_version: Optional[str]
    items: tuple[
        AssistantContextItem,
        ...,
    ]

    @property
    def is_supported(self) -> bool:
        return bool(
            self.items,
        )

    def render(self) -> str:
        if not self.items:
            return ""

        blocks = []

        for index, item in enumerate(
            self.items,
            start=1,
        ):
            blocks.append(
                (
                    f"[{index}] "
                    f"{item.title}\n"
                    f"{item.content}"
                )
            )

        return "\n\n".join(
            blocks,
        )