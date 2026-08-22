import asyncio
import os
import time
from uuid import uuid4

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
ENABLED_ENV_NAME = "CRYPTORADAR_MONITORING_ENABLED"
SCOPE_ENV_NAME = "CRYPTORADAR_MONITORING_SCOPE"
INTERVAL_ENV_NAME = (
    "CRYPTORADAR_MONITORING_INTERVAL_SECONDS"
)


async def main():
    database_url = os.environ.get(
        DATABASE_ENV_NAME,
        "",
    ).strip()

    if not database_url:
        raise SystemExit(
            "CRYPTORADAR_DATABASE_URL não está "
            "configurada nesta sessão."
        )

    scope_key = (
        "local-fastapi-validation-"
        f"{uuid4().hex}"
    )

    previous_enabled = os.environ.get(
        ENABLED_ENV_NAME
    )

    previous_scope = os.environ.get(
        SCOPE_ENV_NAME
    )

    previous_interval = os.environ.get(
        INTERVAL_ENV_NAME
    )

    cleanup_store = (
        PostgreSQLMonitoringStateStore(
            database_url=database_url,
            scope_key=scope_key,
        )
    )

    try:
        print(
            "1/9 Criando alvo temporário ETH..."
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
            "2/9 Estado inicial gravado no Neon."
        )

        os.environ[
            ENABLED_ENV_NAME
        ] = "true"

        os.environ[
            SCOPE_ENV_NAME
        ] = scope_key

        os.environ[
            INTERVAL_ENV_NAME
        ] = "5"

        print(
            "3/9 Configuração temporária "
            "do FastAPI preparada."
        )

        from app.main import app

        print(
            "4/9 Iniciando lifecycle real "
            "do FastAPI..."
        )

        async with app.router.lifespan_context(
            app
        ):
            runtime = (
                app.state.monitoring_runtime
            )

            if runtime is None:
                raise RuntimeError(
                    "O FastAPI não criou "
                    "o MonitoringRuntime."
                )

            if not runtime.is_started:
                raise RuntimeError(
                    "O runtime não foi iniciado."
                )

            if not runtime.is_running:
                raise RuntimeError(
                    "O scheduler não está rodando."
                )

            if (
                runtime.restored_state_count
                != 1
            ):
                raise RuntimeError(
                    "Quantidade inesperada "
                    "de estados restaurados."
                )

            if "ETH" not in (
                runtime.registered_symbols
            ):
                raise RuntimeError(
                    "ETH não foi restaurado."
                )

            print(
                "5/9 FastAPI restaurou ETH "
                "e iniciou o scheduler."
            )

            print(
                "6/9 Aguardando duas "
                "observações reais..."
            )

            deadline = (
                time.monotonic() + 30
            )

            observed_state = None

            while (
                time.monotonic()
                < deadline
            ):
                observed_state = (
                    cleanup_store.load_state(
                        "ETH"
                    )
                )

                if (
                    observed_state
                    is not None
                    and
                    observed_state
                    .observation_count
                    >= 2
                ):
                    break

                await asyncio.sleep(
                    0.5
                )

            if observed_state is None:
                raise RuntimeError(
                    "O estado ETH não foi "
                    "encontrado no Neon."
                )

            if (
                observed_state
                .observation_count
                < 2
            ):
                raise RuntimeError(
                    "O FastAPI não persistiu "
                    "duas observações em "
                    "até 30 segundos."
                )

            if (
                observed_state
                .current_price
                is None
            ):
                raise RuntimeError(
                    "Preço atual ausente."
                )

            if (
                observed_state
                .current_price
                <= 0
            ):
                raise RuntimeError(
                    "Preço atual inválido."
                )

            print(
                "7/9 Monitoramento ativo "
                "confirmado pelo FastAPI."
            )

            print(
                "Preço observado:",
                observed_state.current_price,
            )

            print(
                "Observações:",
                observed_state
                .observation_count,
            )

        if (
            app.state.monitoring_runtime
            is not None
        ):
            raise RuntimeError(
                "O runtime permaneceu "
                "associado ao FastAPI "
                "após o shutdown."
            )

        print(
            "8/9 Shutdown do FastAPI "
            "encerrou o runtime."
        )

        verification_store = (
            PostgreSQLMonitoringStateStore(
                database_url=database_url,
                scope_key=scope_key,
            )
        )

        restored = (
            verification_store.load_state(
                "ETH"
            )
        )

        if restored is None:
            raise RuntimeError(
                "O estado não permaneceu "
                "persistido após o shutdown."
            )

        if (
            restored.observation_count
            < 2
        ):
            raise RuntimeError(
                "As observações não "
                "permaneceram persistidas."
            )

        if restored.current_price is None:
            raise RuntimeError(
                "O preço não permaneceu "
                "persistido."
            )

        print(
            "9/9 Persistência após "
            "shutdown confirmada."
        )

        print()
        print(
            "REAL FASTAPI MONITORING OK"
        )

    finally:
        try:
            cleanup_store.clear()

        except Exception as error:
            print(
                "Aviso na limpeza final:"
            )
            print(
                error
            )

        _restore_environment(
            ENABLED_ENV_NAME,
            previous_enabled,
        )

        _restore_environment(
            SCOPE_ENV_NAME,
            previous_scope,
        )

        _restore_environment(
            INTERVAL_ENV_NAME,
            previous_interval,
        )


def _restore_environment(
    name,
    previous_value,
):
    if previous_value is None:
        os.environ.pop(
            name,
            None,
        )
        return

    os.environ[
        name
    ] = previous_value


if __name__ == "__main__":
    asyncio.run(
        main()
    )