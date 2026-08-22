CREATE TABLE IF NOT EXISTS cryptoradar_monitoring_states (
    scope_key TEXT NOT NULL,
    symbol TEXT NOT NULL,
    state_data JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (
        scope_key,
        symbol
    )
);

CREATE INDEX IF NOT EXISTS
    idx_cryptoradar_monitoring_states_updated_at
ON cryptoradar_monitoring_states (
    updated_at
);