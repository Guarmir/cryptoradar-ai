from typing import Optional

from app.monitoring.coingecko_monitoring_market_data_provider import (
    CoinGeckoMonitoringMarketDataProvider,
)
from app.monitoring.monitoring_cycle_runner import (
    MonitoringCycleRunner,
)
from app.monitoring.monitoring_engine import (
    MonitoringEngine,
)
from app.monitoring.monitoring_runtime import (
    MonitoringRuntime,
)
from app.monitoring.monitoring_runtime_config import (
    MonitoringRuntimeConfig,
)
from app.monitoring.monitoring_scheduler import (
    MonitoringScheduler,
)
from app.monitoring.monitoring_service import (
    MonitoringService,
)
from app.monitoring.postgresql_monitoring_state_store import (
    PostgreSQLMonitoringStateStore,
)


def build_monitoring_runtime(
    config: MonitoringRuntimeConfig,
) -> Optional[MonitoringRuntime]:
    if not config.enabled:
        return None

    database_url = config.database_url
    scope_key = config.scope_key

    if (
        database_url is None
        or scope_key is None
    ):
        raise ValueError(
            "Configuração de monitoramento "
            "incompleta."
        )

    state_store = (
        PostgreSQLMonitoringStateStore(
            database_url=database_url,
            scope_key=scope_key,
        )
    )

    market_data_provider = (
        CoinGeckoMonitoringMarketDataProvider()
    )

    engine = MonitoringEngine()

    service = MonitoringService(
        engine=engine,
        market_data_provider=
            market_data_provider,
        state_store=state_store,
    )

    runner = MonitoringCycleRunner(
        service=service,
    )

    scheduler = MonitoringScheduler(
        runner=runner,
        interval_seconds=
            config.interval_seconds,
    )

    return MonitoringRuntime(
        service=service,
        scheduler=scheduler,
    )