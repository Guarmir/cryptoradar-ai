ALTER TABLE cryptoradar_individual_monitoring_assets
    ADD COLUMN IF NOT EXISTS last_regular_alert_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_emergency_alert_at TIMESTAMPTZ;
