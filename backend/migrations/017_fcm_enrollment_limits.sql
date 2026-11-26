-- Shared enrollment rate limits. Apply only before controlled activation.
CREATE TABLE IF NOT EXISTS cryptoradar_fcm_enrollment_limits (
    scope_key TEXT NOT NULL,
    bucket_key TEXT NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    attempts INTEGER NOT NULL CHECK (attempts > 0),
    PRIMARY KEY (scope_key, bucket_key)
);
CREATE INDEX IF NOT EXISTS idx_cr_fcm_enrollment_limit_expiry
    ON cryptoradar_fcm_enrollment_limits (window_end);
