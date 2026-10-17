import os

from app.push.firebase_admin_push_sender import (
    FirebaseAdminPushSender,
)
from app.push.postgresql_push_device_store import (
    PostgreSQLPushDeviceStore,
)
from app.push.push_delivery_models import (
    PushNotificationMessage,
)
from app.push.push_delivery_service import (
    PushDeliveryService,
)


DATABASE_URL_ENV = (
    "CRYPTORADAR_DATABASE_URL"
)

PUSH_SCOPE_ENV = (
    "CRYPTORADAR_PUSH_SCOPE"
)


def main():
    database_url = os.environ.get(
        DATABASE_URL_ENV,
        "",
    ).strip()

    scope_key = os.environ.get(
        PUSH_SCOPE_ENV,
        "",
    ).strip()

    if not database_url:
        raise RuntimeError(
            "CRYPTORADAR_DATABASE_URL "
            "não está disponível."
        )

    if not scope_key:
        raise RuntimeError(
            "CRYPTORADAR_PUSH_SCOPE "
            "não está disponível."
        )

    store = PostgreSQLPushDeviceStore(
        database_url=database_url,
        scope_key=scope_key,
    )

    enabled_devices = (
        store.load_enabled()
    )

    if len(enabled_devices) != 1:
        raise RuntimeError(
            "A validação exige exatamente "
            "1 dispositivo habilitado. "
            f"Encontrados: {len(enabled_devices)}."
        )

    sender = FirebaseAdminPushSender()

    service = PushDeliveryService(
        device_store=store,
        push_sender=sender,
    )

    result = service.deliver(
        PushNotificationMessage(
            title="CryptoRadar",
            body=(
                "Push real de validação "
                "recebido com sucesso."
            ),
            data={
                "type": "push_validation",
            },
        )
    )

    print(
        "PUSH VALIDATION RESULT"
    )

    print(
        f"total={result.total}"
    )

    print(
        f"delivered={result.delivered}"
    )

    print(
        f"failed={result.failed}"
    )

    print(
        "invalid_destinations="
        f"{result.invalid_tokens}"
    )


if __name__ == "__main__":
    main()