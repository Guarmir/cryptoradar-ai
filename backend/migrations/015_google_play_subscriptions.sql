-- Registros de assinatura verificados pelo servidor.
-- O token de compra nunca deve ser armazenado em texto puro.
-- Esta migracao nao modifica cryptoradar_access_plans.
CREATE TABLE IF NOT EXISTS cryptoradar_google_play_subscriptions (
    id BIGSERIAL PRIMARY KEY,
    scope_key TEXT NOT NULL,
    purchase_token_hash CHAR(64) NOT NULL,
    firebase_auth_uid TEXT NOT NULL,
    package_name TEXT NOT NULL,
    product_id TEXT NOT NULL,
    subscription_state TEXT NOT NULL,
    acknowledgement_state TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    verified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT cryptoradar_gp_subscription_scope_nonempty CHECK (length(btrim(scope_key)) > 0),
    CONSTRAINT cryptoradar_gp_subscription_owner_nonempty CHECK (length(btrim(firebase_auth_uid)) > 0),
    CONSTRAINT cryptoradar_gp_subscription_hash_hex CHECK (purchase_token_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT cryptoradar_gp_subscription_token_unique UNIQUE (scope_key, purchase_token_hash)
);

CREATE INDEX IF NOT EXISTS idx_cryptoradar_gp_subscriptions_owner
    ON cryptoradar_google_play_subscriptions (scope_key, firebase_auth_uid);
