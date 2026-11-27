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
        # Include disabled owned records: a legacy alias must not bypass them.
        groups = {}
        for device in self._devices.load_all():
            groups.setdefault(device.fcm_token, []).append(device)
        allowed = []
        for devices in groups.values():
            try:
                owned = []
                for device in devices:
                    uid = self._owners.load_owner_uid(device.installation_id)
                    if uid is not None:
                        owned.append((device, uid))
                if not owned:
                    allowed.extend(d for d in devices if d.enabled)
                    continue
                # Ambiguous ownership requires recovery, not a legacy fallback.
                if len(owned) != 1:
                    continue
                device, uid = owned[0]
                if not device.enabled:
                    continue
                granted = self._grants.has_access(
                    installation_id=device.installation_id, uid=uid)
                rights = self._rights.pro if granted is True else self._rights.free
                if rights.automatic_market_alerts is True:
                    allowed.append(device)
            except Exception:
                # Fail closed for the whole destination, not just one alias.
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
