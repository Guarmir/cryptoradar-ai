CREATE TABLE IF NOT EXISTS cryptoradar_access_plans (
    scope_key TEXT NOT NULL,
    installation_id TEXT NOT NULL,
    plan TEXT NOT NULL
        CHECK (plan IN ('free', 'pro')),
    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT NOW(),

    PRIMARY KEY (
        scope_key,
        installation_id
    )
);