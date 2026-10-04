from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EarlyMovementConfirmationBlocker:
    key: str
    label: str

    value: Optional[float] = None
    threshold: Optional[float] = None
    distance_ratio: Optional[float] = None

    proximity: str = "unknown"