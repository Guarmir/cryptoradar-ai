
-- CryptoRadar
-- Migration 009: Extreme Movement Discovery Trace
-- Registra os resultados de selecao do Radar Dinamico.
-- Nao modifica tabelas existentes.

CREATE TABLE IF NOT EXISTS
    cryptoradar_extreme_movement_discovery_trace (
        id BIGSERIAL PRIMARY KEY,

        scope_key TEXT NOT NULL,

        observed_at TIMESTAMPTZ NOT NULL,

        universe_size INTEGER NOT NULL
            CHECK (universe_size >= 0),

        candidate_count INTEGER NOT NULL
            CHECK (candidate_count >= 0),

        analyzed_count INTEGER NOT NULL
            CHECK (analyzed_count >= 0),

        excluded_count INTEGER NOT NULL
            CHECK (excluded_count >= 0),

        selected_coin_ids JSONB NOT NULL
            DEFAULT '[]'::jsonb,

        submitted_coin_ids JSONB NOT NULL
            DEFAULT '[]'::jsonb,

        not_submitted_coin_ids JSONB NOT NULL
            DEFAULT '[]'::jsonb
    );

CREATE INDEX IF NOT EXISTS
    idx_extreme_movement_discovery_trace_scope_time
ON cryptoradar_extreme_movement_discovery_trace (
    scope_key,
    observed_at DESC
);
