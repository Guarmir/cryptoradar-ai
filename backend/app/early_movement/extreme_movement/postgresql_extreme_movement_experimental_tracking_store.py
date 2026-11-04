
from typing import Any, Callable, Optional

from app.early_movement.extreme_movement.extreme_movement_experimental_tracking import (
    ExtremeMovementExperimentalTracking,
)


class PostgreSQLExtremeMovementExperimentalTrackingStore:
    TRACKING_TABLE = (
        "cryptoradar_extreme_movement_experimental_tracking"
    )
    HISTORY_TABLE = (
        "cryptoradar_extreme_movement_experimental_price_history"
    )

    def __init__(
        self,
        *,
        database_url: str,
        scope_key: str,
        connection_factory: Optional[Callable[[str], Any]] = None,
    ) -> None:
        if not database_url.strip():
            raise ValueError("URL do PostgreSQL vazia.")
        if not scope_key.strip():
            raise ValueError("Escopo vazio.")

        self._database_url = database_url.strip()
        self._scope_key = scope_key.strip()
        self._connection_factory = connection_factory

    def _connect(self):
        if self._connection_factory is not None:
            return self._connection_factory(self._database_url)

        import psycopg

        return psycopg.connect(self._database_url)

    def load_active(
        self,
    ) -> tuple[
        tuple[int, ExtremeMovementExperimentalTracking], ...
    ]:
        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    SELECT
                        id,
                        coin_id,
                        started_at,
                        last_observed_at,
                        initial_price,
                        latest_price,
                        initial_direction,
                        latest_direction,
                        initial_score,
                        latest_score,
                        initial_evidence_count,
                        latest_evidence_count,
                        latest_state,
                        observation_count,
                        max_observed_price,
                        min_observed_price,
                        status,
                        closed_at,
                        close_reason
                    FROM {self.TRACKING_TABLE}
                    WHERE scope_key = %s
                      AND status = 'active'
                    ORDER BY started_at, id
                    """,
                    (self._scope_key,),
                )

                rows = cursor.fetchall()

                results = []

                for row in rows:
                    tracking = ExtremeMovementExperimentalTracking(
                        coin_id=row[1],
                        started_at=row[2],
                        last_observed_at=row[3],
                        initial_price=row[4],
                        latest_price=row[5],
                        initial_direction=row[6],
                        latest_direction=row[7],
                        initial_score=row[8],
                        latest_score=row[9],
                        initial_evidence_count=row[10],
                        latest_evidence_count=row[11],
                        latest_state=row[12],
                        observation_count=row[13],
                        max_observed_price=row[14],
                        min_observed_price=row[15],
                        status=row[16],
                        closed_at=row[17],
                        close_reason=row[18],
                    )

                    results.append((row[0], tracking))

                connection.commit()
                return tuple(results)

            except Exception:
                connection.rollback()
                raise

            finally:
                cursor.close()

        finally:
            connection.close()

    def save_start(
        self,
        tracking: ExtremeMovementExperimentalTracking,
    ) -> int:
        if tracking.status != "active":
            raise ValueError("Inicio deve estar ativo.")

        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    INSERT INTO {self.TRACKING_TABLE} (
                        scope_key, coin_id, started_at,
                        last_observed_at, initial_price, latest_price,
                        initial_direction, latest_direction,
                        initial_score, latest_score,
                        initial_evidence_count, latest_evidence_count,
                        latest_state, observation_count,
                        max_observed_price, min_observed_price,
                        last_price_at, status
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id
                    """,
                    (
                        self._scope_key,
                        tracking.coin_id,
                        tracking.started_at,
                        tracking.last_observed_at,
                        tracking.initial_price,
                        tracking.latest_price,
                        tracking.initial_direction,
                        tracking.latest_direction,
                        tracking.initial_score,
                        tracking.latest_score,
                        tracking.initial_evidence_count,
                        tracking.latest_evidence_count,
                        tracking.latest_state,
                        tracking.observation_count,
                        tracking.max_observed_price,
                        tracking.min_observed_price,
                        tracking.last_observed_at,
                        tracking.status,
                    ),
                )

                tracking_id = cursor.fetchone()[0]

                self._insert_history(
                    cursor,
                    tracking_id,
                    tracking,
                    is_selected=True,
                )

                connection.commit()
                return tracking_id

            except Exception:
                connection.rollback()
                raise

            finally:
                cursor.close()

        finally:
            connection.close()

    def save_update(
        self,
        tracking_id: int,
        tracking: ExtremeMovementExperimentalTracking,
        *,
        is_selected: bool,
    ) -> None:
        if tracking.status != "active":
            raise ValueError("Atualizacao exige estado ativo.")

        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    UPDATE {self.TRACKING_TABLE}
                    SET last_observed_at = %s,
                        latest_price = %s,
                        latest_direction = %s,
                        latest_score = %s,
                        latest_evidence_count = %s,
                        latest_state = %s,
                        observation_count = %s,
                        max_observed_price = %s,
                        min_observed_price = %s,
                        last_price_at = %s,
                        updated_at = NOW()
                    WHERE id = %s
                      AND scope_key = %s
                      AND coin_id = %s
                      AND status = 'active'
                      AND last_observed_at < %s
                    RETURNING id
                    """,
                    (
                        tracking.last_observed_at,
                        tracking.latest_price,
                        tracking.latest_direction,
                        tracking.latest_score,
                        tracking.latest_evidence_count,
                        tracking.latest_state,
                        tracking.observation_count,
                        tracking.max_observed_price,
                        tracking.min_observed_price,
                        tracking.last_observed_at,
                        tracking_id,
                        self._scope_key,
                        tracking.coin_id,
                        tracking.last_observed_at,
                    ),
                )

                if cursor.fetchone() is None:
                    raise ValueError(
                        "Acompanhamento ausente, encerrado "
                        "ou observacao duplicada."
                    )

                self._insert_history(
                    cursor,
                    tracking_id,
                    tracking,
                    is_selected=is_selected,
                )

                connection.commit()

            except Exception:
                connection.rollback()
                raise

            finally:
                cursor.close()

        finally:
            connection.close()

    def save_close(
        self,
        tracking_id: int,
        tracking: ExtremeMovementExperimentalTracking,
    ) -> None:
        if tracking.status != "closed":
            raise ValueError("Encerramento exige estado fechado.")

        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    UPDATE {self.TRACKING_TABLE}
                    SET status = 'closed',
                        closed_at = %s,
                        close_reason = %s,
                        updated_at = NOW()
                    WHERE id = %s
                      AND scope_key = %s
                      AND coin_id = %s
                      AND status = 'active'
                    RETURNING id
                    """,
                    (
                        tracking.closed_at,
                        tracking.close_reason,
                        tracking_id,
                        self._scope_key,
                        tracking.coin_id,
                    ),
                )

                if cursor.fetchone() is None:
                    raise ValueError(
                        "Acompanhamento nao encontrado ou encerrado."
                    )

                connection.commit()

            except Exception:
                connection.rollback()
                raise

            finally:
                cursor.close()

        finally:
            connection.close()

    def save_batch(
        self,
        *,
        starts: tuple[ExtremeMovementExperimentalTracking, ...] = (),
        updates: tuple[
            tuple[int, ExtremeMovementExperimentalTracking, bool], ...
        ] = (),
        closes: tuple[
            tuple[int, ExtremeMovementExperimentalTracking], ...
        ] = (),
    ) -> tuple[int, ...]:
        """Grava inicios, atualizacoes e encerramentos em uma transacao.

        Retorna os IDs dos novos acompanhamentos na ordem de `starts`.
        O estado do coordenador so deve ser alterado apos retorno com sucesso.
        """
        for tracking in starts:
            if tracking.status != "active":
                raise ValueError("Inicio deve estar ativo.")
        for _, tracking, _ in updates:
            if tracking.status != "active":
                raise ValueError("Atualizacao exige estado ativo.")

        for _, tracking in closes:
            if tracking.status != "closed":
                raise ValueError("Encerramento exige estado fechado.")
            if tracking.closed_at is None or not tracking.close_reason or not tracking.close_reason.strip():
                raise ValueError("Encerramento exige data e motivo.")

        if not starts and not updates and not closes:
            return ()

        connection = self._connect()
        try:
            cursor = connection.cursor()
            try:
                created_ids: list[int] = []
                for tracking in starts:
                    cursor.execute(
                        f"""
                        INSERT INTO {self.TRACKING_TABLE} (
                            scope_key, coin_id, started_at,
                            last_observed_at, initial_price, latest_price,
                            initial_direction, latest_direction,
                            initial_score, latest_score,
                            initial_evidence_count, latest_evidence_count,
                            latest_state, observation_count,
                            max_observed_price, min_observed_price,
                            last_price_at, status
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                        """,
                        (
                            self._scope_key, tracking.coin_id,
                            tracking.started_at, tracking.last_observed_at,
                            tracking.initial_price, tracking.latest_price,
                            tracking.initial_direction, tracking.latest_direction,
                            tracking.initial_score, tracking.latest_score,
                            tracking.initial_evidence_count,
                            tracking.latest_evidence_count,
                            tracking.latest_state, tracking.observation_count,
                            tracking.max_observed_price,
                            tracking.min_observed_price,
                            tracking.last_observed_at, tracking.status,
                        ),
                    )
                    row = cursor.fetchone()
                    if row is None:
                        raise ValueError("Insercao sem ID retornado.")
                    tracking_id = row[0]
                    self._insert_history(
                        cursor, tracking_id, tracking, is_selected=True
                    )
                    created_ids.append(tracking_id)

                for tracking_id, tracking, is_selected in updates:
                    cursor.execute(
                        f"""
                        UPDATE {self.TRACKING_TABLE}
                        SET last_observed_at = %s,
                            latest_price = %s,
                            latest_direction = %s,
                            latest_score = %s,
                            latest_evidence_count = %s,
                            latest_state = %s,
                            observation_count = %s,
                            max_observed_price = %s,
                            min_observed_price = %s,
                            last_price_at = %s,
                            updated_at = NOW()
                        WHERE id = %s
                          AND scope_key = %s
                          AND coin_id = %s
                          AND status = 'active'
                          AND last_observed_at < %s
                        RETURNING id
                        """,
                        (
                            tracking.last_observed_at, tracking.latest_price,
                            tracking.latest_direction, tracking.latest_score,
                            tracking.latest_evidence_count,
                            tracking.latest_state, tracking.observation_count,
                            tracking.max_observed_price,
                            tracking.min_observed_price,
                            tracking.last_observed_at, tracking_id,
                            self._scope_key, tracking.coin_id,
                            tracking.last_observed_at,
                        ),
                    )
                    if cursor.fetchone() is None:
                        raise ValueError(
                            "Acompanhamento ausente, encerrado "
                            "ou observacao duplicada."
                        )
                    self._insert_history(
                        cursor, tracking_id, tracking,
                        is_selected=is_selected,
                    )

                for tracking_id, tracking in closes:
                    cursor.execute(
                        f"""
                        UPDATE {self.TRACKING_TABLE}
                        SET status = 'closed',
                            closed_at = %s,
                            close_reason = %s,
                            updated_at = NOW()
                        WHERE id = %s
                          AND scope_key = %s
                          AND coin_id = %s
                          AND status = 'active'
                          AND last_observed_at <= %s
                        RETURNING id
                        """,
                        (
                            tracking.closed_at,
                            tracking.close_reason,
                            tracking_id,
                            self._scope_key,
                            tracking.coin_id,
                            tracking.closed_at,
                        ),
                    )
                    if cursor.fetchone() is None:
                        raise ValueError(
                            "Acompanhamento ausente, encerrado "
                            "ou encerramento anterior a observacao."
                        )

                connection.commit()
                return tuple(created_ids)
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        finally:
            connection.close()

    def _insert_history(
        self,
        cursor: Any,
        tracking_id: int,
        tracking: ExtremeMovementExperimentalTracking,
        *,
        is_selected: bool,
    ) -> None:
        cursor.execute(
            f"""
            INSERT INTO {self.HISTORY_TABLE} (
                tracking_id,
                observed_at,
                price,
                direction,
                score,
                evidence_count,
                candidate_state,
                is_selected
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                tracking_id,
                tracking.last_observed_at,
                tracking.latest_price,
                tracking.latest_direction,
                tracking.latest_score,
                tracking.latest_evidence_count,
                tracking.latest_state,
                is_selected,
            ),
        )
