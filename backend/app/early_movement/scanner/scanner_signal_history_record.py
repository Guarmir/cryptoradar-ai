from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.early_movement.early_movement_state import (
    EarlyMovementState,
)


@dataclass(frozen=True)
class EarlyMovementScannerSignalHistoryRecord:
    observed_at: datetime

    coin_id: str
    symbol: str
    name: str

    current_price: float
    state: EarlyMovementState
    relevance_score: float

    price_acceleration: Optional[float] = None
    abnormal_volume_ratio: Optional[float] = None
    liquidity_score: Optional[float] = None
    volatility_expansion: Optional[float] = None
    persistence_score: Optional[float] = None
    false_breakout_risk: Optional[float] = None

    support_break: bool = False
    resistance_break: bool = False
    retest_confirmed: bool = False

    breakout_direction: Optional[str] = None

    alertable: bool = False