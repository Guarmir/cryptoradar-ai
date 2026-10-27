
class ExtremeMovementRetentionPolicy:
    DEFAULT_MAX_MISSED_CYCLES = 12

    def __init__(
        self,
        *,
        max_missed_cycles: int = DEFAULT_MAX_MISSED_CYCLES,
    ) -> None:
        if max_missed_cycles < 1:
            raise ValueError(
                "O limite de ciclos deve ser maior que zero."
            )

        self._max_missed_cycles = max_missed_cycles

    def should_close(
        self,
        *,
        missed_cycles: int,
        collection_healthy: bool,
    ) -> bool:
        if missed_cycles < 0:
            raise ValueError(
                "missed_cycles nao pode ser negativo."
            )

        if not collection_healthy:
            return False

        return missed_cycles >= self._max_missed_cycles
