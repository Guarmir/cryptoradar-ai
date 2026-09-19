from typing import Optional

from app.monitoring.coingecko_monitoring_market_data_provider import (
    CoinGeckoMonitoringMarketDataProvider,
)
from app.monitoring.market_event_evaluator import (
    MarketEventEvaluator,
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
from app.push.firebase_admin_push_sender import (
    FirebaseAdminPushSender,
)
from app.push.market_event_push_cooldown import (
    MarketEventPushCooldown,
)
from app.push.market_event_push_message_builder import (
    MarketEventPushMessageBuilder,
)
from app.push.market_event_push_runtime_config import (
    MarketEventPushRuntimeConfig,
)
from app.push.market_event_push_service import (
    MarketEventPushService,
)
from app.push.postgresql_push_device_store import (
    PostgreSQLPushDeviceStore,
)
from app.push.push_delivery_service import (
    PushDeliveryService,
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
            "Configuracao de monitoramento "
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
        market_data_provider=(
            market_data_provider
        ),
        state_store=state_store,
    )

    market_event_evaluator = None
    market_event_callback = None

    push_config = (
        MarketEventPushRuntimeConfig
        .from_environment()
    )

    if push_config.enabled:
        push_database_url = (
            push_config.database_url
        )

        push_scope_key = (
            push_config.scope_key
        )

        if (
            push_database_url is None
            or push_scope_key is None
        ):
            raise ValueError(
                "Configuracao do push de "
                "evento de mercado incompleta."
            )

        device_store = (
            PostgreSQLPushDeviceStore(
                database_url=(
                    push_database_url
                ),
                scope_key=push_scope_key,
            )
        )

        push_sender = (
            FirebaseAdminPushSender()
        )

        delivery_service = (
            PushDeliveryService(
                device_store=device_store,
                push_sender=push_sender,
            )
        )

        market_event_push_service = (
            MarketEventPushService(
                cooldown=(
                    MarketEventPushCooldown(
                        cooldown_seconds=(
                            push_config
                            .cooldown_seconds
                        ),
                    )
                ),
                message_builder=(
                    MarketEventPushMessageBuilder()
                ),
                delivery_service=(
                    delivery_service
                ),
            )
        )

        market_event_evaluator = (
            MarketEventEvaluator(
                minimum_price_change_percent=(
                    push_config
                    .minimum_price_change_percent
                ),
            )
        )

        market_event_callback = (
            market_event_push_service.deliver
        )

    runner = MonitoringCycleRunner(
        service=service,
        market_event_evaluator=(
            market_event_evaluator
        ),
        market_event_callback=(
            market_event_callback
        ),
    )

    scheduler = MonitoringScheduler(
        runner=runner,
        interval_seconds=(
            config.interval_seconds
        ),
    )

    return MonitoringRuntime(
        service=service,
        scheduler=scheduler,
    )