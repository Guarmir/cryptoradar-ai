
CREATE TABLE IF NOT EXISTS
cryptoradar_extreme_movement_directional_history (
    id BIGSERIAL PRIMARY KEY,

    scope_key TEXT NOT NULL,
    coin_id TEXT NOT NULL,

    observed_at TIMESTAMPTZ NOT NULL,

    state TEXT NOT NULL,
    direction TEXT NOT NULL,
    previous_direction TEXT NOT NULL,

    observation_count INTEGER NOT NULL,
    consecutive_moves INTEGER NOT NULL,
    alternating_moves INTEGER NOT NULL,

    latest_price_change_pct DOUBLE PRECISION,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    CONSTRAINT directional_history_unique
        UNIQUE (scope_key, coin_id, observed_at),

    CONSTRAINT directional_history_counts_valid
        CHECK (
            observation_count >= 0
            AND consecutive_moves >= 0
            AND alternating_moves >= 0
        )
);

CREATE INDEX IF NOT EXISTS
idx_extreme_directional_history_coin_time
ON cryptoradar_extreme_movement_directional_history (
    scope_key,
    coin_id,
    observed_at DESC
);
