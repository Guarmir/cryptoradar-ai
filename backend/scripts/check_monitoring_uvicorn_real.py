import os
import sys

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

SCOPE_KEY = "local-uvicorn-validation"


def build_store():
    database_url = os.environ.get(
        DATABASE_ENV_NAME,
        "",
    ).strip()

    if not database_url:
        raise SystemExit(
            "CRYPTORADAR_DATABASE_URL não está "
            "configurada nesta sessão."
        )

    return PostgreSQLMonitoringStateStore(
        database_url=database_url,
        scope_key=SCOPE_KEY,
    )


def prepare():
    store = build_store()

    print(
        "1/3 Limpando escopo temporário..."
    )

    store.clear()

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

    print(
        "2/3 Gravando ETH sem observações..."
    )

    store.save_state(
        state,
    )

    restored = store.load_state(
        "ETH"
    )

    if restored is None:
        raise RuntimeError(
            "ETH não foi gravado."
        )

    if restored.observation_count != 0:
        raise RuntimeError(
            "O alvo inicial deveria possuir "
            "zero observações."
        )

    print(
        "3/3 Estado inicial preparado."
    )

    print()
    print(
        "UVICORN TEST PREPARED"
    )


def verify():
    store = build_store()

    print(
        "1/3 Restaurando ETH após shutdown..."
    )

    state = store.load_state(
        "ETH"
    )

    if state is None:
        raise RuntimeError(
            "ETH não foi encontrado "
            "após o shutdown."
        )

    print(
        "2/3 Conferindo observações..."
    )

    if state.observation_count < 2:
        raise RuntimeError(
            "Foram encontradas menos de "
            "duas observações. "
            f"Quantidade: {state.observation_count}"
        )

    if state.current_price is None:
        raise RuntimeError(
            "Preço atual ausente."
        )

    if state.current_price <= 0:
        raise RuntimeError(
            "Preço atual inválido."
        )

    print(
        "Preço persistido:",
        state.current_price,
    )

    print(
        "Observações persistidas:",
        state.observation_count,
    )

    print(
        "3/3 Persistência após shutdown confirmada."
    )

    print()
    print(
        "REAL UVICORN MONITORING OK"
    )


def cleanup():
    store = build_store()

    print(
        "1/2 Limpando escopo temporário..."
    )

    store.clear()

    remaining = store.load_all()

    if remaining:
        raise RuntimeError(
            "O escopo temporário "
            "não foi totalmente limpo."
        )

    print(
        "2/2 Limpeza confirmada."
    )

    print()
    print(
        "UVICORN TEST CLEANUP OK"
    )


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Use: prepare, verify ou cleanup."
        )

    action = (
        sys.argv[1]
        .strip()
        .lower()
    )

    if action == "prepare":
        prepare()
        return

    if action == "verify":
        verify()
        return

    if action == "cleanup":
        cleanup()
        return

    raise SystemExit(
        "Ação inválida. "
        "Use: prepare, verify ou cleanup."
    )


if __name__ == "__main__":
    main()