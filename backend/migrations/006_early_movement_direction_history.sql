
ALTER TABLE cryptoradar_early_movement_signal_history
ADD COLUMN IF NOT EXISTS
    recent_price_return DOUBLE PRECISION;

ALTER TABLE cryptoradar_early_movement_signal_history
ADD COLUMN IF NOT EXISTS
    direction TEXT;

ALTER TABLE cryptoradar_early_movement_signal_history
ADD CONSTRAINT
    early_movement_direction_valid
CHECK (
    direction IS NULL
    OR direction IN (
        'up',
        'down',
        'neutral'
    )
);
