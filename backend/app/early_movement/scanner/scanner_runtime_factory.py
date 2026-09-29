from typing import Optional

from app.early_movement.scanner.early_movement_scanner import (
    EarlyMovementScanner,
)
from app.early_movement.scanner.scanner_alert_decision import (
    EarlyMovementScannerAlertDecisionMaker,
)
from app.early_movement.scanner.scanner_automation_cycle import (
    EarlyMovementScannerAutomationCycle,
)
from app.early_movement.scanner.scanner_push_cooldown import (
    EarlyMovementScannerPushCooldown,
)
from app.early_movement.scanner.scanner_push_message_builder import (
    EarlyMovementScannerPushMessageBuilder,
)
from app.early_movement.scanner.scanner_push_service import (
    EarlyMovementScannerPushService,
)
from app.early_movement.scanner.scanner_runtime import (
    EarlyMovementScannerRuntime,
)
from app.early_movement.scanner.scanner_runtime_config import (
    EarlyMovementScannerRuntimeConfig,
)
from app.early_movement.scanner.scanner_scheduler import (
    EarlyMovementScannerScheduler,
)
from app.push.firebase_admin_push_sender import (
    FirebaseAdminPushSender,
)
from app.push.postgresql_push_device_store import (
    PostgreSQLPushDeviceStore,
)
from app.push.push_delivery_service import (
    PushDeliveryService,
)


def build_early_movement_scanner_runtime(
    config: EarlyMovementScannerRuntimeConfig,
) -> Optional[EarlyMovementScannerRuntime]:
    if not config.enabled:
        return None

    push_service = None

    if config.push_enabled:
        database_url = config.database_url
        push_scope_key = config.push_scope_key

        if (
            database_url is None
            or push_scope_key is None
        ):
            raise ValueError(
                "Configuracao do push do "
                "scanner incompleta."
            )

        device_store = (
            PostgreSQLPushDeviceStore(
                database_url=database_url,
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

        push_service = (
            EarlyMovementScannerPushService(
                cooldown=(
                    EarlyMovementScannerPushCooldown(
                        cooldown_seconds=(
                            config
                            .push_cooldown_seconds
                        ),
                    )
                ),
                message_builder=(
                    EarlyMovementScannerPushMessageBuilder()
                ),
                delivery_service=delivery_service,
            )
        )

    cycle = (
        EarlyMovementScannerAutomationCycle(
            scanner=EarlyMovementScanner(),
            alert_decision_maker=(
                EarlyMovementScannerAlertDecisionMaker()
            ),
            push_service=push_service,
        )
    )

    scheduler = EarlyMovementScannerScheduler(
        cycle=cycle,
        interval_seconds=(
            config.interval_seconds
        ),
    )

    return EarlyMovementScannerRuntime(
        scheduler=scheduler,
    )