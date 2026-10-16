
CREATE TABLE IF NOT EXISTS
    cryptoradar_early_movement_notification_state (
        scope_key TEXT NOT NULL,
        coin_id TEXT NOT NULL,

        last_notified_state TEXT NOT NULL,
        last_notified_at TIMESTAMPTZ NOT NULL,

        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

        PRIMARY KEY (scope_key, coin_id)
    );

CREATE INDEX IF NOT EXISTS
    idx_early_movement_notification_updated
ON cryptoradar_early_movement_notification_state (
    scope_key,
    updated_at DESC
);
