CREATE TABLE IF NOT EXISTS
    cryptoradar_early_movement_signal_history (
        id BIGSERIAL PRIMARY KEY,

        scope_key TEXT NOT NULL,

        observed_at TIMESTAMPTZ NOT NULL,

        coin_id TEXT NOT NULL,
        symbol TEXT NOT NULL,
        name TEXT NOT NULL,

        current_price DOUBLE PRECISION NOT NULL,
        state TEXT NOT NULL,
        relevance_score DOUBLE PRECISION NOT NULL,

        price_acceleration DOUBLE PRECISION,
        abnormal_volume_ratio DOUBLE PRECISION,
        liquidity_score DOUBLE PRECISION,
        volatility_expansion DOUBLE PRECISION,
        persistence_score DOUBLE PRECISION,
        false_breakout_risk DOUBLE PRECISION,

        support_break BOOLEAN NOT NULL DEFAULT FALSE,
        resistance_break BOOLEAN NOT NULL DEFAULT FALSE,
        retest_confirmed BOOLEAN NOT NULL DEFAULT FALSE,

        breakout_direction TEXT,

        alertable BOOLEAN NOT NULL DEFAULT FALSE,

        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

CREATE INDEX IF NOT EXISTS
    idx_early_movement_history_scope_observed
ON cryptoradar_early_movement_signal_history (
    scope_key,
    observed_at DESC
);

CREATE INDEX IF NOT EXISTS
    idx_early_movement_history_coin_observed
ON cryptoradar_early_movement_signal_history (
    scope_key,
    coin_id,
    observed_at DESC
);

CREATE INDEX IF NOT EXISTS
    idx_early_movement_history_alertable
ON cryptoradar_early_movement_signal_history (
    scope_key,
    alertable,
    observed_at DESC
);