ALTER TABLE cryptoradar_individual_monitoring_assets
    ADD COLUMN IF NOT EXISTS alert_interval_minutes INTEGER NOT NULL DEFAULT 30,
    ADD COLUMN IF NOT EXISTS emergency_alert_enabled BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE cryptoradar_individual_monitoring_assets
    DROP CONSTRAINT IF EXISTS individual_alert_interval_valid;
ALTER TABLE cryptoradar_individual_monitoring_assets
    ADD CONSTRAINT individual_alert_interval_valid CHECK (alert_interval_minutes IN (5,15,30,60));
