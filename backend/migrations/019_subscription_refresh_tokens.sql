-- Encrypted purchase credentials for server-side revalidation. No plaintext tokens.
CREATE TABLE IF NOT EXISTS cryptoradar_subscription_refresh_tokens (
    subscription_scope TEXT NOT NULL,
    package_name TEXT NOT NULL,
    purchase_token_hash TEXT NOT NULL,
    firebase_auth_uid TEXT NOT NULL,
    encrypted_token TEXT NOT NULL,
    next_check_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (subscription_scope, package_name, purchase_token_hash)
);
CREATE INDEX IF NOT EXISTS idx_subscription_refresh_due
    ON cryptoradar_subscription_refresh_tokens (subscription_scope, package_name, next_check_at);
