"""Opt-in filtering for the global monitoring producer, not scanner alerts."""
import os


class CommercialMonitoringDeviceStore:
    """Read-only recipient adapter. Never changes device or monitoring state."""
    def __init__(self, *, device_store, owner_store, grant_reader, entitlements_config):
        self._devices = device_store
        self._owners = owner_store
        self._grants = grant_reader
        self._rights = entitlements_config

    def load_enabled(self):
        allowed = []
        for device in self._devices.load_enabled():
            try:
                uid = self._owners.load_owner_uid(device.installation_id)
                if uid is None:
                    # Existing unowned installations keep legacy delivery.
                    allowed.append(device)
                    continue
                granted = self._grants.has_access(
                    installation_id=device.installation_id, uid=uid)
                rights = self._rights.pro if granted is True else self._rights.free
                if rights.automatic_market_alerts is True:
                    allowed.append(device)
            except Exception:
                # Unknown ownership or entitlement must not authorize delivery.
                continue
        return tuple(allowed)


def monitoring_delivery_store(*, device_store, database_url, scope_key):
    if os.getenv('GOOGLE_PLAY_MONITORING_ACCESS_ENABLED', '').strip().lower() != 'true':
        return device_store
    from app.billing.subscription_installation_access import create_installation_access_service
    from app.push.postgresql_push_installation_owner_store import PostgreSQLPushInstallationOwnerStore
    service = create_installation_access_service()
    reader = service.reader
    if reader.url != database_url or reader.push_scope != scope_key:
        raise ValueError('Escopo de autorizacao comercial diferente do push.')
    return CommercialMonitoringDeviceStore(
        device_store=device_store,
        owner_store=PostgreSQLPushInstallationOwnerStore(
            database_url=database_url, scope_key=scope_key),
        grant_reader=reader,
        entitlements_config=service.config,
    )
