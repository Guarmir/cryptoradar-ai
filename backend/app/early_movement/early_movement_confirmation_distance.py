from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EarlyMovementConfirmationDistance:
    key: str
    passed: bool

    value: Optional[float] = None
    threshold: Optional[float] = None

    distance_ratio: Optional[float] = None

    @property
    def proximity(self) -> str:
        if self.passed:
            return "confirmed"

        if self.distance_ratio is None:
            return "unknown"

        if self.distance_ratio <= 0.10:
            return "near"

        if self.distance_ratio <= 0.30:
            return "insufficient"

        return "far"