from typing import Any, Callable, Optional

from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner.scanner_signal_history_record import (
    EarlyMovementScannerSignalHistoryRecord,
)
from app.early_movement.scanner.scanner_signal_history_store import (
    EarlyMovementScannerSignalHistoryStore,
)


class PostgreSQLEarlyMovementScannerSignalHistoryStore(
    EarlyMovementScannerSignalHistoryStore
):
    TABLE_NAME = (
        "cryptoradar_early_movement_signal_history"
    )

    def __init__(
        self,
        *,
        database_url: str,
        scope_key: str,
        connection_factory: Optional[
            Callable[[str], Any]
        ] = None,
    ) -> None:
        normalized_database_url = (
            database_url.strip()
        )

        normalized_scope_key = (
            scope_key.strip()
        )

        if not normalized_database_url:
            raise ValueError(
                "A URL do PostgreSQL "
                "não pode ser vazia."
            )

        if not normalized_scope_key:
            raise ValueError(
                "O escopo do histórico "
                "não pode ser vazio."
            )

        self._database_url = (
            normalized_database_url
        )

        self._scope_key = (
            normalized_scope_key
        )

        self._connection_factory = (
            connection_factory
        )

    @property
    def scope_key(
        self,
    ) -> str:
        return self._scope_key

    def save(
        self,
        record: EarlyMovementScannerSignalHistoryRecord,
    ) -> None:
        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME} (
                        scope_key,
                        observed_at,
                        coin_id,
                        symbol,
                        name,
                        current_price,
                        state,
                        relevance_score,
                        price_acceleration,
                        abnormal_volume_ratio,
                        liquidity_score,
                        volatility_expansion,
                        persistence_score,
                        false_breakout_risk,
                        support_break,
                        resistance_break,
                        retest_confirmed,
                        breakout_direction,
                        alertable
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s
                    )
                    """,
                    (
                        self._scope_key,
                        record.observed_at,
                        record.coin_id,
                        record.symbol,
                        record.name,
                        record.current_price,
                        record.state.value,
                        record.relevance_score,
                        record.price_acceleration,
                        record.abnormal_volume_ratio,
                        record.liquidity_score,
                        record.volatility_expansion,
                        record.persistence_score,
                        record.false_breakout_risk,
                        record.support_break,
                        record.resistance_break,
                        record.retest_confirmed,
                        record.breakout_direction,
                        record.alertable,
                    ),
                )

                connection.commit()

            except Exception:
                connection.rollback()
                raise

            finally:
                cursor.close()

        finally:
            connection.close()

    def load_recent(
        self,
        *,
        limit: int = 100,
    ) -> tuple[
        EarlyMovementScannerSignalHistoryRecord,
        ...,
    ]:
        if limit < 1:
            raise ValueError(
                "O limite deve ser maior que zero."
            )

        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    SELECT
                        observed_at,
                        coin_id,
                        symbol,
                        name,
                        current_price,
                        state,
                        relevance_score,
                        price_acceleration,
                        abnormal_volume_ratio,
                        liquidity_score,
                        volatility_expansion,
                        persistence_score,
                        false_breakout_risk,
                        support_break,
                        resistance_break,
                        retest_confirmed,
                        breakout_direction,
                        alertable
                    FROM {self.TABLE_NAME}
                    WHERE scope_key = %s
                    ORDER BY observed_at DESC, id DESC
                    LIMIT %s
                    """,
                    (
                        self._scope_key,
                        limit,
                    ),
                )

                rows = cursor.fetchall()

            finally:
                cursor.close()

        finally:
            connection.close()

        return tuple(
            self._record_from_row(
                row,
            )
            for row in rows
        )

    def _connect(
        self,
    ):
        if self._connection_factory is not None:
            return self._connection_factory(
                self._database_url,
            )

        import psycopg

        return psycopg.connect(
            self._database_url,
        )

    @staticmethod
    def _record_from_row(
        row,
    ) -> EarlyMovementScannerSignalHistoryRecord:
        return EarlyMovementScannerSignalHistoryRecord(
            observed_at=row[0],
            coin_id=row[1],
            symbol=row[2],
            name=row[3],
            current_price=row[4],
            state=EarlyMovementState(
                row[5]
            ),
            relevance_score=row[6],
            price_acceleration=row[7],
            abnormal_volume_ratio=row[8],
            liquidity_score=row[9],
            volatility_expansion=row[10],
            persistence_score=row[11],
            false_breakout_risk=row[12],
            support_break=row[13],
            resistance_break=row[14],
            retest_confirmed=row[15],
            breakout_direction=row[16],
            alertable=row[17],
        )