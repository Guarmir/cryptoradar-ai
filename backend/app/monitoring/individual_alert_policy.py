"""Personalized alert decisions on fresh, consecutive market observations.

No execution of trades or delivery of notifications. Thresholds are heuristics,
not liquidation estimates or measured position P&L.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite


@dataclass(frozen=True)
class IndividualAlertSettings:
    interval_minutes: int = 30
    emergency_enabled: bool = True

    def __post_init__(self):
        if type(self.interval_minutes) is not int or self.interval_minutes not in (5, 15, 30, 60):
            raise ValueError('Periodicidade invalida.')
        if type(self.emergency_enabled) is not bool:
            raise ValueError('Configuracao emergencial invalida.')


@dataclass(frozen=True)
class IndividualAlertDecision:
    kind: str
    change_percent: float
    observed_at: datetime


def evaluate_alert(*, state, interpretation, settings, last_regular=None,
                   last_emergency=None, now=None):
    """Return one candidate, with emergency taking precedence over regular.

    Only consecutive observations within five minutes are accepted. A regular
    alert requires a meaningful movement; emergency applies only to adverse
    position movements. Both timers are independent; actual delivery must
    persist its own deduplication state.
    """
    now = now if now is not None else datetime.now(timezone.utc)
    current = state.current_observation
    previous = state.previous_observation
    change = state.price_change_since_previous_percent
    if current is None or previous is None or change is None or not isfinite(change):
        return None
    stamp = current.observed_at
    if any(t.tzinfo is None or t.utcoffset() is None for t in (stamp, previous.observed_at, now)):
        return None
    age = (now - stamp).total_seconds()
    gap = (stamp - previous.observed_at).total_seconds()
    if not 0 <= age <= 180 or not 0 < gap <= 300:
        return None
    if interpretation not in ('upward_movement', 'downward_movement', 'favorable_movement', 'adverse_movement'):
        return None

    def due(last, seconds):
        if last is None:
            return True
        if last.tzinfo is None or last.utcoffset() is None:
            return False
        return (stamp - last).total_seconds() >= seconds

    if settings.emergency_enabled and interpretation == 'adverse_movement' and abs(change) >= 2:
        if due(last_emergency, 300):
            return IndividualAlertDecision('emergency', change, stamp)
        return None
    if abs(change) >= 0.5 and due(last_regular, settings.interval_minutes * 60):
        return IndividualAlertDecision('regular', change, stamp)
    return None
