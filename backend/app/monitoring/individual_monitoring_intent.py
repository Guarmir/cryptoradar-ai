"""Intent-specific interpretation of observed price changes, not trade signals."""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class MonitoringIntent:
    intent: str = 'opportunity'
    side: str | None = None

    def __post_init__(self):
        if not ((self.intent == 'opportunity' and self.side is None)
                or (self.intent == 'position' and self.side in ('long', 'short'))):
            raise ValueError('Intencao ou direcao invalida.')


def interpret_observation(state, intent):
    change = state.price_change_since_previous_percent
    if change is None or not isfinite(change):
        return 'insufficient_data'
    if change == 0:
        return 'unchanged'
    if intent.intent == 'opportunity':
        return 'upward_movement' if change > 0 else 'downward_movement'
    favorable = (change > 0) == (intent.side == 'long')
    return 'favorable_movement' if favorable else 'adverse_movement'
