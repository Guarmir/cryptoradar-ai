
-- Migration 010
-- Persistencia da comparacao experimental do Radar Dinamico.
-- Preserva os registros existentes e a estrutura original.

ALTER TABLE cryptoradar_extreme_movement_discovery_trace
    ADD COLUMN IF NOT EXISTS experimental_status TEXT
        NOT NULL DEFAULT 'not_available',
    ADD COLUMN IF NOT EXISTS experimental_coin_ids JSONB
        NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS experimental_only_coin_ids JSONB
        NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS common_coin_ids JSONB
        NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS experimental_priorities JSONB
        NOT NULL DEFAULT '[]'::jsonb;
