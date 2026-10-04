from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EarlyMovementConfirmationCriterion:
    key: str
    label: str
    passed: bool

    value: Optional[float] = None
    threshold: Optional[float] = None

    reason: Optional[str] = None