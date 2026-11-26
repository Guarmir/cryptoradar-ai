-- Temporary verified authorization; not a permanent PRO plan.
CREATE TABLE IF NOT EXISTS cryptoradar_subscription_installation_grants (
    push_scope TEXT NOT NULL,
    installation_id TEXT NOT NULL,
    firebase_auth_uid TEXT NOT NULL,
    subscription_scope TEXT NOT NULL,
    purchase_token_hash TEXT NOT NULL,
    valid_until TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (push_scope, installation_id),
    FOREIGN KEY (push_scope, installation_id)
        REFERENCES cryptoradar_push_devices (scope_key, installation_id) ON DELETE CASCADE
);
