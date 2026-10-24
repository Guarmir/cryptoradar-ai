
ALTER TABLE cryptoradar_early_movement_signal_history
ADD COLUMN IF NOT EXISTS
    recent_price_return DOUBLE PRECISION;

ALTER TABLE cryptoradar_early_movement_signal_history
ADD COLUMN IF NOT EXISTS
    direction TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'early_movement_direction_valid'
          AND conrelid = (
              'cryptoradar_early_movement_signal_history'::regclass
          )
    ) THEN
        ALTER TABLE cryptoradar_early_movement_signal_history
        ADD CONSTRAINT early_movement_direction_valid
        CHECK (
            direction IS NULL
            OR direction IN (
                'up',
                'down',
                'neutral'
            )
        );
    END IF;
END
$$;
