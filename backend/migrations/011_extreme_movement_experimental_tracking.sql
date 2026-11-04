-- Migration 011
-- Acompanhamento experimental de candidatos do Radar Dinamico.
-- Mantem os dados separados do scanner conservador e de suas notificacoes.
-- Conferir a estrutura existente no Neon antes de executar esta migracao.

CREATE TABLE IF NOT EXISTS cryptoradar_extreme_movement_experimental_tracking (
    id BIGSERIAL PRIMARY KEY,
    scope_key TEXT NOT NULL,
    coin_id TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    last_observed_at TIMESTAMPTZ NOT NULL,
    initial_price DOUBLE PRECISION NOT NULL CHECK (initial_price > 0),
    latest_price DOUBLE PRECISION NOT NULL CHECK (latest_price > 0),
    initial_direction TEXT NOT NULL,
    latest_direction TEXT NOT NULL,
    initial_score DOUBLE PRECISION NOT NULL,
    latest_score DOUBLE PRECISION NOT NULL,
    initial_evidence_count INTEGER NOT NULL CHECK (initial_evidence_count >= 0),
    latest_evidence_count INTEGER NOT NULL CHECK (latest_evidence_count >= 0),
    latest_state TEXT NOT NULL,
    observation_count INTEGER NOT NULL CHECK (observation_count >= 1),
    max_observed_price DOUBLE PRECISION NOT NULL CHECK (max_observed_price > 0),
    min_observed_price DOUBLE PRECISION NOT NULL CHECK (min_observed_price > 0),
    last_price_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'closed')),
    closed_at TIMESTAMPTZ,
    close_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT extreme_tracking_closed_fields_check CHECK (
        (status = 'active' AND closed_at IS NULL)
        OR (status = 'closed' AND closed_at IS NOT NULL AND close_reason IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_extreme_experimental_tracking_scope_status
    ON cryptoradar_extreme_movement_experimental_tracking (scope_key, status, started_at);

CREATE UNIQUE INDEX IF NOT EXISTS idx_extreme_experimental_tracking_active_coin
    ON cryptoradar_extreme_movement_experimental_tracking (scope_key, coin_id)
    WHERE status = 'active';

CREATE TABLE IF NOT EXISTS cryptoradar_extreme_movement_experimental_price_history (
    id BIGSERIAL PRIMARY KEY,
    tracking_id BIGINT NOT NULL REFERENCES cryptoradar_extreme_movement_experimental_tracking(id) ON DELETE CASCADE,
    observed_at TIMESTAMPTZ NOT NULL,
    price DOUBLE PRECISION NOT NULL CHECK (price > 0),
    direction TEXT NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    evidence_count INTEGER NOT NULL CHECK (evidence_count >= 0),
    candidate_state TEXT NOT NULL,
    is_selected BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT extreme_experimental_history_unique_observation UNIQUE (tracking_id, observed_at)
);

CREATE INDEX IF NOT EXISTS idx_extreme_experimental_history_tracking_time
    ON cryptoradar_extreme_movement_experimental_price_history (tracking_id, observed_at DESC);
