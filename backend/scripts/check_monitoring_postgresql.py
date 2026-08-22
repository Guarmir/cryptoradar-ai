import os
from uuid import uuid4

from app.monitoring.monitoring_observation import (
    MonitoringObservation,
)
from app.monitoring.monitoring_state import (
    MonitoringState,
)
from app.monitoring.monitoring_target import (
    MonitoringTarget,
)
from app.monitoring.postgresql_monitoring_state_store import (
    PostgreSQLMonitoringStateStore,
)


DATABASE_ENV_NAME = "CRYPTORADAR_DATABASE_URL"


def main():
    database_url = os.environ.get(
        DATABASE_ENV_NAME,
        "",
    ).strip()

    if not database_url:
        raise SystemExit(
            "CRYPTORADAR_DATABASE_URL não está configurada."
        )

    scope_key = (
        "local-validation-"
        f"{uuid4().hex}"
    )

    cleanup_store = (
        PostgreSQLMonitoringStateStore(
            database_url=database_url,
            scope_key=scope_key,
        )
    )

    try:
        print(
            "1/5 Criando estado de teste..."
        )

        target = MonitoringTarget(
            symbol="ETH",
            coin_id="ethereum",
            trading_mode="futures",
            has_open_position=True,
            position_side="short",
            entry_price=3200,
            leverage=5,
        )

        state = MonitoringState(
            target=target,
        )

        state = state.observe(
            MonitoringObservation(
                symbol="ETH",
                price=3150,
                volume=750_000_000,
                market_cap=380_000_000_000,
                change_24h=-2.4,
            )
        )

        print(
            "2/5 Gravando no PostgreSQL..."
        )

        store_a = (
            PostgreSQLMonitoringStateStore(
                database_url=database_url,
                scope_key=scope_key,
            )
        )

        store_a.save_state(
            state,
        )

        print(
            "3/5 Abrindo novo store e restaurando..."
        )

        store_b = (
            PostgreSQLMonitoringStateStore(
                database_url=database_url,
                scope_key=scope_key,
            )
        )

        restored = store_b.load_state(
            "eth",
        )

        if restored is None:
            raise RuntimeError(
                "O estado gravado não foi restaurado."
            )

        if restored.target.symbol != "ETH":
            raise RuntimeError(
                "Símbolo restaurado incorretamente."
            )

        if not restored.target.is_short:
            raise RuntimeError(
                "Direção SHORT não foi restaurada."
            )

        if restored.target.entry_price != 3200:
            raise RuntimeError(
                "Preço de entrada não foi restaurado."
            )

        if restored.target.leverage != 5:
            raise RuntimeError(
                "Alavancagem não foi restaurada."
            )

        if restored.observation_count != 1:
            raise RuntimeError(
                "Contador de observações não foi restaurado."
            )

        if restored.current_price != 3150:
            raise RuntimeError(
                "Preço observado não foi restaurado."
            )

        print(
            "4/5 Persistência real confirmada."
        )

        all_states = store_b.load_all()

        if len(all_states) != 1:
            raise RuntimeError(
                "Quantidade inesperada de estados "
                "no escopo temporário."
            )

        removed = store_b.delete_state(
            "ETH",
        )

        if not removed:
            raise RuntimeError(
                "O registro temporário não pôde ser removido."
            )

        if store_b.load_state("ETH") is not None:
            raise RuntimeError(
                "O registro temporário permaneceu no banco."
            )

        print(
            "5/5 Limpeza confirmada."
        )

        print()
        print(
            "POSTGRESQL MONITORING STORE OK"
        )

    finally:
        try:
            cleanup_store.clear()

        except Exception as error:
            print(
                "Aviso: não foi possível "
                "executar a limpeza final:"
            )
            print(
                error,
            )


if __name__ == "__main__":
    main()