-- CryptoRadar
-- Migration 007
-- Extreme Movement Observation Persistence
--
-- Estrutura independente do scanner conservador.
-- Nao altera tabelas existentes.

CREATE TABLE IF NOT EXISTS
    cryptoradar_extreme_movement_observation_history (
        id BIGSERIAL PRIMARY KEY,

        scope_key TEXT NOT NULL,

        observed_at TIMESTAMPTZ NOT NULL,

        coin_id TEXT NOT NULL,
        symbol TEXT NOT NULL,
        name TEXT NOT NULL,

        state TEXT NOT NULL,
        direction TEXT NOT NULL,

        relevance_score DOUBLE PRECISION NOT NULL,
        supporting_evidence_count INTEGER NOT NULL,

        maturity_level TEXT NOT NULL,

        observation_change TEXT NOT NULL,

        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

        CONSTRAINT chk_extreme_history_evidence
            CHECK (supporting_evidence_count >= 0),

        CONSTRAINT chk_extreme_history_relevance
            CHECK (
                relevance_score >= 0
                AND relevance_score <= 100
            )
    );


CREATE INDEX IF NOT EXISTS
    idx_extreme_history_scope_observed
ON cryptoradar_extreme_movement_observation_history (
    scope_key,
    observed_at DESC,
    id DESC
);


CREATE INDEX IF NOT EXISTS
    idx_extreme_history_coin_observed
ON cryptoradar_extreme_movement_observation_history (
    scope_key,
    coin_id,
    observed_at DESC,
    id DESC
);


CREATE TABLE IF NOT EXISTS
    cryptoradar_extreme_movement_active_observations (
        id BIGSERIAL PRIMARY KEY,

        scope_key TEXT NOT NULL,

        coin_id TEXT NOT NULL,
        symbol TEXT NOT NULL,
        name TEXT NOT NULL,

        state TEXT NOT NULL,
        direction TEXT NOT NULL,

        relevance_score DOUBLE PRECISION NOT NULL,
        supporting_evidence_count INTEGER NOT NULL,

        maturity_level TEXT NOT NULL,

        observation_status TEXT NOT NULL DEFAULT 'active',

        missed_cycles INTEGER NOT NULL DEFAULT 0,

        first_observed_at TIMESTAMPTZ NOT NULL,
        last_observed_at TIMESTAMPTZ NOT NULL,

        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

        CONSTRAINT uq_extreme_active_scope_coin
            UNIQUE (scope_key, coin_id),

        CONSTRAINT chk_extreme_active_evidence
            CHECK (supporting_evidence_count >= 0),

        CONSTRAINT chk_extreme_active_relevance
            CHECK (
                relevance_score >= 0
                AND relevance_score <= 100
            ),

        CONSTRAINT chk_extreme_active_missed
            CHECK (missed_cycles >= 0),

        CONSTRAINT chk_extreme_active_status
            CHECK (
                observation_status IN (
                    'active',
                    'awaiting_update',
                    'closed'
                )
            ),

        CONSTRAINT chk_extreme_active_dates
            CHECK (
                last_observed_at >= first_observed_at
            )
    );


CREATE INDEX IF NOT EXISTS
    idx_extreme_active_scope_status
ON cryptoradar_extreme_movement_active_observations (
    scope_key,
    observation_status,
    last_observed_at DESC
);


CREATE INDEX IF NOT EXISTS
    idx_extreme_active_scope_updated
ON cryptoradar_extreme_movement_active_observations (
    scope_key,
    updated_at DESC
);