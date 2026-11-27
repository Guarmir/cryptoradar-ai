-- Watchlist belongs to a verified account, not a device or a ticker.
CREATE TABLE IF NOT EXISTS cryptoradar_individual_monitoring_assets (
    scope_key TEXT NOT NULL CHECK (length(btrim(scope_key)) > 0),
    firebase_auth_uid TEXT NOT NULL CHECK (length(btrim(firebase_auth_uid)) > 0),
    coin_id TEXT NOT NULL CHECK (length(coin_id) BETWEEN 1 AND 200 AND coin_id = lower(btrim(coin_id))),
    symbol TEXT NOT NULL CHECK (length(symbol) BETWEEN 1 AND 50 AND symbol = upper(btrim(symbol))),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (scope_key, firebase_auth_uid, coin_id)
);
