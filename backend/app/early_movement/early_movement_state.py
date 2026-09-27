from enum import Enum


class EarlyMovementState(str, Enum):
    NORMAL = "normal"
    OBSERVATION = "observation"
    EARLY_MOVEMENT = "early_movement"
    CONFIRMED_MOVEMENT = "confirmed_movement"
    EXHAUSTION_OR_POSSIBLE_REVERSAL = "exhaustion_or_possible_reversal"