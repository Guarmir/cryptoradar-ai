-- Existing watchlists default to opportunity observation.
ALTER TABLE cryptoradar_individual_monitoring_assets
    ADD COLUMN IF NOT EXISTS intent TEXT NOT NULL DEFAULT 'opportunity',
    ADD COLUMN IF NOT EXISTS position_side TEXT;
ALTER TABLE cryptoradar_individual_monitoring_assets
    DROP CONSTRAINT IF EXISTS individual_monitoring_intent_valid;
ALTER TABLE cryptoradar_individual_monitoring_assets
    ADD CONSTRAINT individual_monitoring_intent_valid CHECK (
        (intent = 'opportunity' AND position_side IS NULL) OR
        (intent = 'position' AND position_side IS NOT NULL AND position_side IN ('long', 'short'))
    );
