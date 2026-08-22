import os
import time
from uuid import uuid4

from app.monitoring.monitoring_runtime_config import (
    MonitoringRuntimeConfig,
)
from app.monitoring.monitoring_runtime_factory import (
    build_monitoring_runtime,
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
            "CRYPTORADAR_DATABASE_URL não está configurada "
            "nesta sessão do terminal."
        )

    scope_key = (
        "local-runtime-validation-"
        f"{uuid4().hex}"
    )

    cleanup_store = (
        PostgreSQLMonitoringStateStore(
            database_url=database_url,
            scope_key=scope_key,
        )
    )

    runtime = None

    try:
        print(
            "1/8 Criando alvo temporário ETH..."
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

        initial_state = MonitoringState(
            target=target,
        )

        cleanup_store.save_state(
            initial_state,
        )

        print(
            "2/8 Alvo gravado no PostgreSQL."
        )

        config = MonitoringRuntimeConfig(
            enabled=True,
            database_url=database_url,
            scope_key=scope_key,
            interval_seconds=5,
        )

        runtime = build_monitoring_runtime(
            config,
        )

        if runtime is None:
            raise RuntimeError(
                "O runtime não foi criado."
            )

        print(
            "3/8 Iniciando runtime real..."
        )

        started = runtime.start()

        if not started:
            raise RuntimeError(
                "O runtime não pôde ser iniciado."
            )

        if runtime.restored_state_count != 1:
            raise RuntimeError(
                "Quantidade inesperada de estados restaurados."
            )

        if runtime.target_count != 1:
            raise RuntimeError(
                "Quantidade inesperada de alvos ativos."
            )

        if "ETH" not in runtime.registered_symbols:
            raise RuntimeError(
                "ETH não foi restaurado pelo runtime."
            )

        print(
            "4/8 Runtime restaurou ETH e iniciou o scheduler."
        )

        print(
            "5/8 Aguardando duas observações reais..."
        )

        deadline = time.monotonic() + 30

        observed_state = None

        while time.monotonic() < deadline:
            observed_state = (
                cleanup_store.load_state(
                    "ETH"
                )
            )

            if (
                observed_state is not None
                and observed_state.observation_count >= 2
            ):
                break

            time.sleep(
                0.5
            )

        if observed_state is None:
            raise RuntimeError(
                "O estado ETH desapareceu do PostgreSQL."
            )

        if observed_state.observation_count < 2:
            raise RuntimeError(
                "O scheduler não conseguiu persistir "
                "duas observações reais em até 30 segundos."
            )

        if observed_state.current_price is None:
            raise RuntimeError(
                "A observação não possui preço atual."
            )

        if observed_state.current_price <= 0:
            raise RuntimeError(
                "O preço observado é inválido."
            )

        print(
            "6/8 Duas observações reais confirmadas."
        )

        print(
            "Preço atual observado:",
            observed_state.current_price,
        )

        print(
            "Observações:",
            observed_state.observation_count,
        )

        runtime.stop()
        runtime = None

        print(
            "7/8 Runtime encerrado. "
            "Abrindo novo acesso ao PostgreSQL..."
        )

        verification_store = (
            PostgreSQLMonitoringStateStore(
                database_url=database_url,
                scope_key=scope_key,
            )
        )

        restored = verification_store.load_state(
            "ETH"
        )

        if restored is None:
            raise RuntimeError(
                "O estado não permaneceu persistido "
                "após o encerramento do runtime."
            )

        if restored.target.coin_id != "ethereum":
            raise RuntimeError(
                "coin_id restaurado incorretamente."
            )

        if restored.observation_count < 2:
            raise RuntimeError(
                "As observações não permaneceram "
                "persistidas."
            )

        if restored.current_price is None:
            raise RuntimeError(
                "O preço não permaneceu persistido."
            )

        print(
            "8/8 Persistência após shutdown confirmada."
        )

        print()
        print(
            "REAL MONITORING RUNTIME OK"
        )

    finally:
        if runtime is not None:
            try:
                runtime.stop()
            except Exception as error:
                print(
                    "Aviso ao encerrar runtime:"
                )
                print(
                    error
                )

        try:
            cleanup_store.clear()

        except Exception as error:
            print(
                "Aviso: não foi possível executar "
                "a limpeza final:"
            )
            print(
                error
            )


if __name__ == "__main__":
    main()