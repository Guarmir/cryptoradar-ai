"""Opt-in account-directed alerts; no broadcast or private lock-screen payload."""
from datetime import datetime, timezone
import logging

from app.monitoring.individual_alert_policy import IndividualAlertSettings, evaluate_alert
from app.push.push_device import PushDevice
from app.push.push_delivery_models import PushNotificationMessage

logger = logging.getLogger(__name__)


class PostgreSQLIndividualAlertStore:
    def __init__(self, *, access, scope_key, connection_factory=None):
        self.reader = access.reader
        self.config = access.config
        self.scope = scope_key
        self.factory = connection_factory

    def _connect(self):
        if self.factory is not None:
            return self.factory(self.reader.url)
        import psycopg
        return psycopg.connect(self.reader.url, connect_timeout=10,
                               options='-c statement_timeout=10000')

    def load_settings(self, asset):
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute('''SELECT alert_interval_minutes, emergency_alert_enabled,
                last_regular_alert_at, last_emergency_alert_at
                FROM cryptoradar_individual_monitoring_assets
                WHERE scope_key = %s AND firebase_auth_uid = %s AND coin_id = %s
                  AND intent = %s AND position_side IS NOT DISTINCT FROM %s''',
                (self.scope, asset.uid, asset.coin_id, asset.intent, asset.side))
            row = cur.fetchone()
            return None if row is None else (IndividualAlertSettings(*row[:2]), *row[2:])

    def recipients(self, asset):
        # Fresh per-installation grant and rank, not a cached account entitlement.
        # Deny any ambiguous owned token, even when the other registration is disabled.
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute('''WITH ranked AS (
                SELECT coin_id, intent, position_side, row_number() OVER
                    (ORDER BY created_at, coin_id) AS rn
                FROM cryptoradar_individual_monitoring_assets
                WHERE scope_key = %s AND firebase_auth_uid = %s
            ), eligible AS (
                SELECT d.installation_id, d.fcm_token, d.platform, d.enabled,
                       d.firebase_installation_id, r.rn,
                       EXISTS (SELECT 1 FROM cryptoradar_subscription_installation_grants g
                         JOIN cryptoradar_google_play_subscriptions s
                           ON s.scope_key = g.subscription_scope
                          AND s.purchase_token_hash = g.purchase_token_hash
                          AND s.firebase_auth_uid = g.firebase_auth_uid
                         WHERE g.push_scope = d.scope_key AND g.installation_id = d.installation_id
                           AND g.firebase_auth_uid = o.firebase_auth_uid
                           AND g.subscription_scope = %s AND s.package_name = %s
                           AND s.product_id = 'cryptoradar_pro_monthly'
                           AND g.valid_until > NOW() AND s.expires_at > NOW()
                           AND s.verified_at > NOW() - INTERVAL '15 minutes'
                           AND s.subscription_state IN ('SUBSCRIPTION_STATE_ACTIVE',
                               'SUBSCRIPTION_STATE_IN_GRACE_PERIOD', 'SUBSCRIPTION_STATE_CANCELED')
                           AND s.acknowledgement_state = 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED') AS pro
                FROM cryptoradar_push_devices d
                JOIN cryptoradar_push_installation_owners o
                  ON o.scope_key = d.scope_key AND o.installation_id = d.installation_id
                CROSS JOIN ranked r
                WHERE d.scope_key = %s AND o.firebase_auth_uid = %s AND d.enabled
                  AND r.coin_id = %s AND r.intent = %s AND r.position_side IS NOT DISTINCT FROM %s
                  AND NOT EXISTS (SELECT 1 FROM cryptoradar_push_devices other
                    JOIN cryptoradar_push_installation_owners oo
                      ON oo.scope_key = other.scope_key AND oo.installation_id = other.installation_id
                    WHERE other.scope_key = d.scope_key AND other.fcm_token = d.fcm_token
                      AND other.installation_id <> d.installation_id)
            ) SELECT installation_id, fcm_token, platform, enabled, firebase_installation_id
              FROM eligible WHERE CASE WHEN pro THEN %s AND rn <= %s
                                         ELSE %s AND rn <= %s END
              ORDER BY installation_id''',
                (self.scope, asset.uid, self.reader.subscription_scope, self.reader.package,
                 self.reader.push_scope, asset.uid, asset.coin_id, asset.intent, asset.side,
                 self.config.pro.automatic_market_alerts, self.config.pro.monitored_asset_limit,
                 self.config.free.automatic_market_alerts, self.config.free.monitored_asset_limit))
            return tuple(PushDevice(*row) for row in cur.fetchall())

    def reserve(self, asset, settings, decision):
        # Atomic compare-and-set, before sending: at-most-once attempt across workers.
        if decision.kind == 'emergency':
            column, seconds = 'last_emergency_alert_at', 300
        elif decision.kind == 'regular':
            column, seconds = 'last_regular_alert_at', settings.interval_minutes * 60
        else:
            raise ValueError('Unknown alert kind.')
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(f'''UPDATE cryptoradar_individual_monitoring_assets
                SET {column} = %s
                WHERE scope_key = %s AND firebase_auth_uid = %s AND coin_id = %s
                  AND intent = %s AND position_side IS NOT DISTINCT FROM %s
                  AND alert_interval_minutes = %s AND emergency_alert_enabled = %s
                  AND %s BETWEEN NOW() - INTERVAL '3 minutes' AND NOW()
                  AND ({column} IS NULL OR {column} <= %s - (%s * INTERVAL '1 second'))
                RETURNING coin_id''',
                (decision.observed_at, self.scope, asset.uid, asset.coin_id, asset.intent,
                 asset.side, settings.interval_minutes, settings.emergency_enabled,
                 decision.observed_at, decision.observed_at, seconds))
            return cur.fetchone() is not None


class IndividualAlertDelivery:
    def __init__(self, *, store, sender, clock=None):
        self.store = store
        self.sender = sender
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def deliver(self, asset, state, interpretation):
        loaded = self.store.load_settings(asset)
        if loaded is None:
            return 0
        settings, regular, emergency = loaded
        decision = evaluate_alert(state=state, interpretation=interpretation,
            settings=settings, last_regular=regular, last_emergency=emergency, now=self.clock())
        if decision is None:
            return 0
        devices = self.store.recipients(asset)
        if not devices or not self.store.reserve(asset, settings, decision):
            return 0
        # Until account-switch/token recovery is validated, do not expose coin,
        # position, price or account identity on a potentially stale device.
        message = PushNotificationMessage(
            title='CryptoRadar — Alerta prioritário' if decision.kind == 'emergency' else 'CryptoRadar — Monitoramento',
            body='Abra o aplicativo para conferir o monitoramento.',
            data={'type': 'individual_monitoring', 'priority': decision.kind})
        delivered = 0
        attempted = set()
        for device in devices:
            if not device.can_receive_push or device.fcm_token in attempted:
                continue
            attempted.add(device.fcm_token)
            try:
                if self.sender.send(device=device, message=message).delivered:
                    delivered += 1
            except Exception:
                logger.warning('Individual alert send unavailable.')
        return delivered
