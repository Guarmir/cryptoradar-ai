-- Migration 008: Extreme Movement observation prices
-- The discovery price is preserved from the first observation.
-- Existing records remain NULL when historical prices are unavailable.

ALTER TABLE cryptoradar_extreme_movement_active_observations
    ADD COLUMN IF NOT EXISTS discovery_price DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS discovery_price_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS latest_price DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS latest_price_at TIMESTAMPTZ;
