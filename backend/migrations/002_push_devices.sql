CREATE TABLE IF NOT EXISTS cryptoradar_push_devices (
    scope_key TEXT NOT NULL,
    installation_id TEXT NOT NULL,
    fcm_token TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'android',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (
        scope_key,
        installation_id
    )
);

CREATE INDEX IF NOT EXISTS
    idx_cryptoradar_push_devices_enabled
ON cryptoradar_push_devices (
    scope_key,
    enabled
);

CREATE INDEX IF NOT EXISTS
    idx_cryptoradar_push_devices_updated_at
ON cryptoradar_push_devices (
    updated_at
);